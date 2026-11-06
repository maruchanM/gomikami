import PyWorker from "./py.worker.ts?worker";

export interface TestResult {
  file: string;
  name: string;
  ok: boolean;
  message: string;
}

export interface Analysis {
  error: string | null;
  metrics?: Record<string, number>;
  bad_names?: string[];
  /** 監査部に見つかった禁止事項。1つでもあればコードは実行しない */
  audit?: string[];
}

export interface RunResult {
  timeout: boolean;
  tests: TestResult[];
}

const RUN_TIMEOUT_MS = 3000;
const ANALYZE_TIMEOUT_MS = 5000;
const SPARES = 2;

interface Slot {
  worker: Worker;
  ready: Promise<void>;
  isReady: boolean;
  pending: Map<number, { resolve: (v: any) => void; reject: (e: Error) => void }>;
}

function spawnSlot(): Slot {
  const worker = new PyWorker();
  const pending: Slot["pending"] = new Map();
  const slot: Slot = { worker, pending, isReady: false, ready: Promise.resolve() };
  slot.ready = new Promise((resolve, reject) => {
    worker.addEventListener("message", (e) => {
      const msg = e.data;
      if (msg.type === "ready") {
        slot.isReady = true;
        return resolve();
      }
      if (msg.type === "load-error") return reject(new Error(msg.error));
      const job = pending.get(msg.id);
      if (!job) return;
      pending.delete(msg.id);
      msg.ok ? job.resolve(msg.result) : job.reject(new Error(msg.error));
    });
  });
  return slot;
}

function killSlot(slot: Slot) {
  slot.worker.terminate();
  for (const job of slot.pending.values()) job.reject(new Error("worker restarted"));
  slot.pending.clear();
}

/**
 * Pyodide を載せた Worker の管理。固まったり落ちたりしたら Worker ごと作り直す。
 * 採点(analyze)とテスト実行(run)は別インスタンスに分け、プレイヤーのコードが採点側に触れないようにする。
 * disposable にすると run のたびに Worker を捨てる（改ざんを次の実行に持ち越させない）。
 * 予備を SPARES 個先に起動しておき、連続実行でもなるべく待たせない。
 */
export class PyRunner {
  private current: Slot;
  private spares: Slot[] = [];
  private nextId = 0;

  constructor(private opts: { disposable?: boolean } = {}) {
    this.current = spawnSlot();
    if (opts.disposable) for (let i = 0; i < SPARES; i++) this.spares.push(spawnSlot());
  }

  get ready() {
    return this.current.ready;
  }

  /** 次の run がすぐ始められるか（false なら Pyodide の起動待ちが発生する） */
  get isReady() {
    return this.current.isReady;
  }

  private respawn() {
    killSlot(this.current);
    this.current = this.spares.shift() ?? spawnSlot();
    if (this.opts.disposable) this.spares.push(spawnSlot());
  }

  /** timeoutMs 以内に返事がなければ "timeout"。どちらでも失敗したら Worker を作り直す */
  private async call<T>(kind: string, payload: unknown, timeoutMs: number): Promise<T | "timeout"> {
    const slot = this.current;
    await slot.ready;
    const id = this.nextId++;
    let timer: number | undefined;
    const job = new Promise<T>((resolve, reject) => {
      slot.pending.set(id, { resolve, reject });
      slot.worker.postMessage({ id, kind, payload });
    });
    const timeout = new Promise<"timeout">((resolve) => {
      timer = window.setTimeout(() => resolve("timeout"), timeoutMs);
    });
    try {
      const result = await Promise.race([job, timeout]);
      if (result === "timeout") this.respawn();
      return result;
    } catch (err) {
      this.respawn();
      throw err;
    } finally {
      window.clearTimeout(timer);
    }
  }

  /** 解析できなかった（固まった・落ちた）場合は監査違反として扱う */
  async analyze(source: string): Promise<Analysis> {
    try {
      const result = await this.call<Analysis>("analyze", source, ANALYZE_TIMEOUT_MS);
      if (result !== "timeout") return result;
    } catch {
      // 下で解析不能として返す
    }
    return { error: "解析不能", audit: ["解析不能なコード"] };
  }

  async run(files: Record<string, string>, tests: Record<string, string>): Promise<RunResult> {
    let result: TestResult[] | "timeout";
    try {
      result = await this.call<TestResult[]>("run", { workdir: "/home/pyodide/work", files, tests }, RUN_TIMEOUT_MS);
    } catch {
      result = "timeout";
    }
    if (this.opts.disposable && result !== "timeout") this.respawn();
    return result === "timeout" ? { timeout: true, tests: [] } : { timeout: false, tests: result };
  }
}
