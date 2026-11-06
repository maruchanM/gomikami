export interface StageEvent {
  type: "spec_change";
  atSec: number;
  tests: string;
  /** 一緒に追加される抜き打ち検査（期待値は画面に出さない） */
  hiddenTests?: string;
  /** 目標値の切り替え先（targets.json のキー） */
  solution?: string;
  /** この神度以上で ALL GREEN になったら、atSec を待たずに発生する */
  orWhenKamido?: number;
  message: string;
}

export interface Stage {
  id: string;
  title: string;
  subtitle: string;
  ticket: string;
  timeLimitSec: number;
  undoLimit: number;
  /** 抜き打ち検査（期待値は画面に出さない。テストの答えの丸暗記対策） */
  hiddenTests?: string;
  events: StageEvent[];
  files: Record<string, string>;
  /** 模範解答の指標（tools/check_stages.py が生成） */
  targets: Record<string, Record<string, number>>;
}

// 模範解答はブラウザに配信しない（指標だけ targets.json で渡す）
const raw = import.meta.glob(["../stages/*/*", "!../stages/*/solution*.py"], {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<
  string,
  string
>;

function loadStages(): Stage[] {
  const byId = new Map<string, Record<string, string>>();
  for (const [path, content] of Object.entries(raw)) {
    const [, id, file] = path.match(/stages\/([^/]+)\/([^/]+)$/)!;
    if (!byId.has(id)) byId.set(id, {});
    byId.get(id)![file] = content;
  }
  return [...byId.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, files]) => ({ id, ...JSON.parse(files["stage.json"]), files, targets: JSON.parse(files["targets.json"]) }));
}

export const STAGES = loadStages();
