import type { EditorView } from "@codemirror/view";
import { createEditor } from "./editor";
import type { Analysis, PyRunner, TestResult } from "./pyrunner";
import { damageQuip, quipFor } from "./quips";
import { kamido, type MetricPart, type Metrics, rankOf } from "./scoring";
import type { Stage, StageEvent } from "./stages";

const MAX_HP = 100;
const FAIL_PENALTY = 10;
/** モーダルのボタンが押せるようになるまで（打鍵中の Enter で誤って閉じないように） */
const MODAL_LOCK_MS = 1200;
/** デバッグ用: ?speed=20 で時間が20倍速で進む */
const SPEED = Number(new URLSearchParams(location.search).get("speed")) || 1;

export type GameOutcome =
  | { kind: "clear"; stage: Stage; kamido: number; parts: MetricPart[]; hp: number; remainingSec: number }
  | { kind: "gameover"; stage: Stage; title: string; reason: string }
  | { kind: "quit" };

interface Execution {
  /** 監査・無限ループ・テスト失敗のどれにも引っかからなかった */
  green: boolean;
  audit: string[];
  metrics: Metrics | null;
}

const html = String.raw;

function bar(value: number, max: number, cells = 10, on = "■", off = "□") {
  const filled = Math.round((value / max) * cells);
  return on.repeat(filled) + off.repeat(cells - filled);
}

export function mmss(sec: number) {
  return `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}`;
}

function auditHint(audit: string[]) {
  if (audit.some((a) => a.startsWith("import") || a.startsWith("from"))) {
    return "使えるのは datetime, math, calendar, itertools, functools, decimal, collections, enum, dataclasses, typing などの基本的なものだけです。";
  }
  if (audit.some((a) => a.includes("解析不能") || a.includes("巨大"))) return "人間が読める長さで書いてください。";
  return "リフレクションや内部属性に頼らず、素直に書いてください。";
}

export function escapeHtml(s: string) {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}

export class GameSession {
  private hp = MAX_HP;
  private remaining: number;
  private undoLeft: number;
  private elapsed = 0;
  private paused = true;
  private busy = false;
  private finished = false;
  private timerId = 0;
  private firedEvents = new Set<StageEvent>();
  private activeTests: Record<string, string>;
  private original!: Metrics;
  private target: Metrics;
  private lastMetrics: Metrics | null = null;
  private lastKamido = 0;
  private mainEditor!: EditorView;
  private editors = new Map<string, EditorView>();
  private onKey = (e: KeyboardEvent) => this.handleKey(e);
  private el!: HTMLElement;

  constructor(
    private root: HTMLElement,
    private stage: Stage,
    /** 採点専用。プレイヤーのコードは一切実行しない */
    private judge: PyRunner,
    /** テスト実行専用 */
    private runner: PyRunner,
    private onEnd: (outcome: GameOutcome) => void,
  ) {
    this.remaining = stage.timeLimitSec;
    this.undoLeft = stage.undoLimit;
    this.activeTests = { "tests.py": stage.files["tests.py"] };
    if (stage.hiddenTests) this.activeTests[stage.hiddenTests] = stage.files[stage.hiddenTests];
    this.target = stage.targets["solution.py"];
    this.render();
  }

  async start() {
    this.log("技術的負債をスキャン中...");
    this.original = (await this.judge.analyze(this.stage.files["main.py"])).metrics!;
    this.updateKamido(this.original);
    this.log("スキャン完了。", "ok");
    window.addEventListener("keydown", this.onKey, true);
    this.timerId = window.setInterval(() => this.tick(), 1000 / SPEED);
    const briefed = localStorage.getItem("gomikami.briefed") === "1";
    localStorage.setItem("gomikami.briefed", "1");
    await this.dialog(
      briefed ? `STAGE ${this.stage.id.slice(0, 2)}: ${this.stage.title}` : "作戦説明",
      (briefed ? this.shortBriefing() : this.fullBriefing()).join("\n"),
      [{ label: "了解", value: true }],
    );
  }

  private fullBriefing() {
    return [
      "・main.py を書き直して「神度」を上げろ",
      "・tests.py は仕様。全部通したまま直すこと",
      `・テストが赤いまま [実行] すると 信用度 -${FAIL_PENALTY}。0 で炎上`,
      `・Ctrl+Z (Undo) は ${this.stage.undoLimit} 回まで`,
      "・[提出] は ALL GREEN の時だけ受理される",
      "・exec や sys などの黒魔術は監査部が見ている（実行すら許されない）",
      "　使えるモジュール:",
      "　　datetime, math, calendar, itertools, functools,",
      "　　decimal, collections, enum, dataclasses, typing など",
      "・画面に出ていない「抜き打ち検査」もある。仕様どおりに書くこと",
      `・制限時間 ${mmss(this.stage.timeLimitSec)}。何が起きても慌てないこと`,
    ];
  }

  /** 2回目以降はルール説明を省いて依頼内容だけ */
  private shortBriefing() {
    return [
      this.stage.ticket,
      "",
      `制限時間 ${mmss(this.stage.timeLimitSec)} / Undo ${this.stage.undoLimit} 回 / 抜き打ち検査あり`,
      "（ルールは前と同じ。Ctrl+Enter で実行）",
    ];
  }

  private render() {
    const s = this.stage;
    this.root.innerHTML = html`
      <div class="game">
        <header class="hud">
          <span class="hud-stage">STAGE ${s.id.slice(0, 2)}: ${escapeHtml(s.title)}</span>
          <span>TIME <b id="timer"></b></span>
          <span>信用度 <b id="hp"></b></span>
          <span>Undo残 <b id="undo"></b></span>
        </header>
        <div class="kamido-row">
          神度 <span id="kbar" class="kbar"></span> <b id="kscore">--</b> <span id="krank" class="krank"></span>
        </div>
        <main class="game-main">
          <section class="panel editor-pane">
            <nav class="tabs" id="tabs"></nav>
            <div class="editors" id="editors"></div>
          </section>
          <aside class="side">
            <div class="panel"><h3>チケット</h3><pre class="ticket">${escapeHtml(s.ticket)}</pre></div>
            <div class="panel"><h3>テスト <span id="test-summary"></span></h3><ul class="tests" id="tests"><li class="dim">まだ実行していません</li></ul></div>
            <div class="panel"><h3>指標 (いま / 元 → 目標)</h3><table class="metrics" id="metrics"></table></div>
            <div class="panel log-panel"><h3>ログ</h3><div class="log" id="log"></div></div>
          </aside>
        </main>
        <footer class="actions">
          <button id="run">[Ctrl+Enter] 実行</button>
          <button id="submit">[Ctrl+S] 提出</button>
          <span class="dim small hint">テストが赤いまま実行すると信用度 -${FAIL_PENALTY}</span>
          <button id="quit" class="dim-btn">[Esc] 逃げる</button>
        </footer>
        <div class="modal hidden" id="modal"></div>
      </div>`;
    this.el = this.root.querySelector<HTMLElement>(".game")!;
    this.mainEditor = createEditor(this.$("#editors"), {
      doc: s.files["main.py"],
      onUndo: () => this.consumeUndo(),
    });
    this.editors.set("main.py", this.mainEditor);
    this.addTab("main.py");
    this.addTab("tests.py");
    this.$("#run").addEventListener("click", () => this.run());
    this.$("#submit").addEventListener("click", () => this.submit());
    this.$("#quit").addEventListener("click", () => this.quit());
    this.updateHud();
  }

  private $(sel: string) {
    return this.el.querySelector<HTMLElement>(sel)!;
  }

  // ------------------------------------------------------------ タブとエディタ

  private addTab(name: string) {
    const tab = document.createElement("button");
    tab.className = "tab";
    tab.textContent = name === "main.py" ? name : `${name} [RO]`;
    tab.dataset.file = name;
    tab.addEventListener("click", () => this.showTab(name));
    this.$("#tabs").append(tab);
    this.showTab(this.el.querySelector<HTMLElement>(".tab.active")?.dataset.file ?? name);
  }

  private showTab(name: string) {
    if (!this.editors.has(name)) {
      this.editors.set(name, createEditor(this.$("#editors"), { doc: this.activeTests[name], readOnly: true }));
    }
    for (const [file, view] of this.editors) view.dom.classList.toggle("hidden", file !== name);
    for (const tab of this.el.querySelectorAll<HTMLElement>(".tab")) tab.classList.toggle("active", tab.dataset.file === name);
    if (name === "main.py") this.mainEditor.focus();
  }

  private consumeUndo() {
    if (this.undoLeft <= 0) {
      this.log("Undo の在庫が尽きました。過去は変えられない。", "warn");
      return false;
    }
    this.undoLeft--;
    this.updateHud();
    return true;
  }

  // ------------------------------------------------------------ 進行

  private handleKey(e: KeyboardEvent) {
    if (this.finished || this.paused) return;
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key === "Enter") this.run();
    else if (mod && e.key.toLowerCase() === "s") this.submit();
    else if (e.key === "Escape") void this.quit();
    else return;
    e.preventDefault();
    e.stopPropagation();
  }

  private tick() {
    if (this.paused || this.finished) return;
    this.elapsed++;
    this.remaining--;
    this.updateHud();
    for (const ev of this.stage.events) {
      if (this.elapsed >= ev.atSec) void this.fire(ev);
    }
    if (this.remaining <= 0) this.deadline();
  }

  private async fire(ev: StageEvent) {
    if (this.firedEvents.has(ev) || this.finished) return;
    this.firedEvents.add(ev);
    this.activeTests[ev.tests] = this.stage.files[ev.tests];
    if (ev.hiddenTests) this.activeTests[ev.hiddenTests] = this.stage.files[ev.hiddenTests];
    this.addTab(ev.tests);
    if (ev.solution) {
      this.target = this.stage.targets[ev.solution];
      this.updateKamido(this.lastMetrics ?? this.original);
    }
    this.log(`仕様変更: ${ev.tests} が追加されました`, "warn");
    await this.dialog("!!! 仕様変更 !!!", ev.message, [{ label: "OK（しぶしぶ）", value: true }]);
  }

  /** CRT 風ダイアログ。開いている間はタイマーが止まり、キー操作も効かない */
  private dialog<T>(title: string, message: string, buttons: { label: string; value: T }[], lockMs = MODAL_LOCK_MS) {
    this.paused = true;
    const modal = this.$("#modal");
    modal.innerHTML = html`
      <div class="window">
        <div class="window-title">${escapeHtml(title)}</div>
        <pre>${escapeHtml(message)}</pre>
        <div class="window-buttons">${buttons.map((b) => `<button disabled>${escapeHtml(b.label)}</button>`).join("")}</div>
      </div>`;
    modal.classList.remove("hidden");
    (document.activeElement as HTMLElement | null)?.blur();
    const els = [...modal.querySelectorAll<HTMLButtonElement>("button")];
    setTimeout(() => {
      els.forEach((b) => (b.disabled = false));
      els[0].focus();
    }, lockMs);
    return new Promise<T>((resolve) => {
      els.forEach((btn, i) =>
        btn.addEventListener("click", () => {
          modal.classList.add("hidden");
          this.paused = false;
          this.mainEditor.focus();
          resolve(buttons[i].value);
        }),
      );
    });
  }

  private async execute(): Promise<Execution | null> {
    if (this.busy || this.paused || this.finished) return null;
    this.busy = true;
    this.el.classList.add("busy");
    this.log("実行中...");
    try {
      const source = this.mainEditor.state.doc.toString();
      const analysis = await this.judge.analyze(source);
      if (analysis.audit?.length) return this.audited(analysis.audit);
      if (!this.runner.isReady) this.log("テスト用サーバーを再起動しています…（毎回）", "info");
      const result = await this.runner.run({ "main.py": source }, this.activeTests);
      if (result.timeout) {
        this.log("応答なし。無限ループの疑い。サーバーを再起動しています...", "err");
        this.damage();
        return { green: false, audit: [], metrics: null };
      }
      return this.showResult(result.tests, analysis);
    } finally {
      this.busy = false;
      this.el.classList.remove("busy");
    }
  }

  private audited(audit: string[]): Execution {
    this.log(`監査部: 禁止事項を検出 → ${audit.join(", ")}。実行を差し止めました。`, "err");
    this.log(`監査部: ${auditHint(audit)}`, "warn");
    this.damage();
    return { green: false, audit, metrics: null };
  }

  private showResult(rawTests: TestResult[], analysis: Analysis): Execution {
    let surprise = 0;
    const tests = rawTests.map((t) =>
      t.file.startsWith("hidden_")
        ? { ...t, name: `抜き打ち検査 #${++surprise}`, message: t.ok ? "" : "期待値は非公開。仕様どおりに動いていません。" }
        : t,
    );
    const failed = tests.filter((t) => !t.ok);
    this.$("#test-summary").textContent = `${tests.length - failed.length}/${tests.length}`;
    const list = this.$("#tests");
    list.innerHTML = [...failed, ...tests.filter((t) => t.ok)]
      .map(
        (t) => html`<li class="${t.ok ? "ok" : "err"}">${t.ok ? "[PASS]" : "[FAIL]"} ${escapeHtml(t.name)}${
          t.ok ? "" : `<pre>${escapeHtml(t.message)}</pre>`
        }</li>`,
      )
      .join("");
    list.scrollTop = 0;
    const metrics = analysis.metrics ?? null;
    const before = this.lastKamido;
    if (metrics) this.updateKamido(metrics);
    if (failed.length) {
      this.log(`テスト失敗 ${failed.length}件。`, "err");
      if (failed.every((t) => t.file.startsWith("hidden_"))) {
        this.log("レビュアー: 公開テストだけ通る…それ、テストの答えを暗記しただけですよね？", "warn");
      }
      this.damage();
      return { green: false, audit: [], metrics };
    }
    this.log("ALL GREEN.", "ok");
    if (metrics) this.log(`レビュアー: ${quipFor(metrics, analysis.bad_names ?? [], this.lastKamido, before)}`, "warn");
    for (const ev of this.stage.events) {
      if (ev.orWhenKamido !== undefined && this.lastKamido >= ev.orWhenKamido) void this.fire(ev);
    }
    return { green: true, audit: [], metrics };
  }

  private damage() {
    this.hp = Math.max(0, this.hp - FAIL_PENALTY);
    this.log(`信用度 -${FAIL_PENALTY}。${damageQuip(this.hp)}`, "err");
    this.updateHud();
    document.body.classList.remove("shake");
    void document.body.offsetWidth;
    document.body.classList.add("shake");
    if (this.hp <= 0) {
      this.end({ kind: "gameover", stage: this.stage, title: "炎上", reason: "あなたの信用度はゼロになりました。" });
    }
  }

  private run() {
    void this.execute();
  }

  private async submit(atDeadline = false) {
    const result = await this.execute();
    if (!result || this.finished) return;
    if (result.audit.length) {
      if (atDeadline) {
        this.end({
          kind: "gameover",
          stage: this.stage,
          title: "監査部に連行されました",
          reason: `最終提出物から禁止事項（${result.audit.join(", ")}）が見つかりました。`,
        });
      } else {
        this.log("監査部により差し戻されました。", "warn");
      }
      return;
    }
    if (!result.green) {
      if (atDeadline) this.end({ kind: "gameover", stage: this.stage, title: "納期遅延", reason: "テストが赤いまま時間切れです。" });
      else this.log("提出却下。テストを全部通してから出直してください。", "warn");
      return;
    }
    // この実行で仕様変更が発生したなら、新しいテストで確かめ直させる
    if (this.paused) return;
    const { score, parts } = kamido(this.original, this.target, result.metrics!);
    this.end({ kind: "clear", stage: this.stage, kamido: score, parts, hp: this.hp, remainingSec: Math.max(0, this.remaining) });
  }

  /** 実行中なら次の tick で再挑戦する */
  private deadline() {
    if (this.busy) return;
    this.log("時間切れ！自動提出します。", "warn");
    void this.submit(true);
  }

  private async quit() {
    const ok = await this.dialog(
      "確認",
      "本当に逃げますか？\n（進捗は破棄され、あなたの名前が git blame に残ります）",
      [
        { label: "戻る", value: false },
        { label: "逃げる", value: true },
      ],
      0,
    );
    if (ok) this.end({ kind: "quit" });
  }

  private end(outcome: GameOutcome) {
    if (this.finished) return;
    this.finished = true;
    window.clearInterval(this.timerId);
    window.removeEventListener("keydown", this.onKey, true);
    for (const view of this.editors.values()) view.destroy();
    this.onEnd(outcome);
  }

  // ------------------------------------------------------------ 表示

  private updateHud() {
    const timer = this.$("#timer");
    timer.textContent = mmss(Math.max(0, this.remaining));
    timer.classList.toggle("danger", this.remaining <= 60);
    const hp = this.$("#hp");
    hp.textContent = `${bar(this.hp, MAX_HP)} ${this.hp}`;
    hp.classList.toggle("danger", this.hp <= 30);
    this.$("#undo").textContent = String(this.undoLeft);
  }

  private updateKamido(current: Metrics) {
    this.lastMetrics = current;
    const { score, parts } = kamido(this.original, this.target, current);
    this.lastKamido = score;
    const rank = rankOf(score);
    this.$("#kbar").textContent = `[${bar(score, 100, 20, "█", "░")}]`;
    this.$("#kscore").textContent = String(score);
    this.$("#krank").textContent = `(${rank.name})`;
    this.$("#metrics").innerHTML = parts
      .map((p) => {
        const cls = p.score === null ? "dim" : p.score >= 1 ? "ok" : p.current > p.original ? "err" : "";
        return html`<tr class="${cls}"><td>${p.label}</td><td class="num">${p.current}</td><td class="num dim">${p.original} → ${p.target}</td></tr>`;
      })
      .join("");
  }

  private log(message: string, level: "info" | "ok" | "warn" | "err" = "info") {
    const line = document.createElement("div");
    line.className = level;
    line.textContent = `[${mmss(this.elapsed)}] ${message}`;
    const log = this.$("#log");
    log.append(line);
    log.scrollTop = log.scrollHeight;
  }
}
