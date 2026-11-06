export const METRICS = [
  { key: "complexity", label: "循環的複雑度", weight: 25 },
  { key: "nesting", label: "ネストの深さ", weight: 15 },
  { key: "duplication", label: "コピペ行数", weight: 20 },
  { key: "length", label: "最長の関数", weight: 10 },
  { key: "naming", label: "ダメな名前", weight: 15 },
  { key: "magic", label: "マジックナンバー", weight: 5 },
  { key: "globals", label: "グローバル状態", weight: 10 },
  { key: "longlines", label: "長すぎる行", weight: 5 },
  { key: "tricks", label: "小細工", weight: 10 },
] as const;

export type Metrics = Record<string, number>;

export interface MetricPart {
  key: string;
  label: string;
  original: number;
  target: number;
  current: number;
  /** 0〜1。null は改善の余地がなく採点対象外 */
  score: number | null;
}

/** 元コードからの改善率で神度(0〜100)を出す。改善余地のない指標は、悪化させた時だけ採点対象になる。 */
export function kamido(original: Metrics, target: Metrics, current: Metrics) {
  let earned = 0;
  let total = 0;
  const parts: MetricPart[] = METRICS.map(({ key, label, weight }) => {
    const o = original[key];
    const t = target[key];
    const c = current[key];
    let score: number | null;
    if (o > t) score = Math.min(1, Math.max(0, (o - c) / (o - t)));
    else score = c > Math.max(o, t) ? 0 : null;
    if (score !== null) {
      earned += score * weight;
      total += weight;
    }
    return { key, label, original: o, target: t, current: c, score };
  });
  return { score: total === 0 ? 100 : Math.round((earned / total) * 100), parts };
}

export const RANKS = [
  { min: 90, name: "神", comment: "元のコードを書いた人が泣いて謝った" },
  { min: 70, name: "良コード", comment: "後輩に見せても恥ずかしくない" },
  { min: 45, name: "普通", comment: "レビューは通る。たぶん" },
  { min: 20, name: "クソ", comment: "動くだけマシ" },
  { min: 0, name: "ゴミ", comment: "悪化してない？" },
];

export function rankOf(score: number) {
  return RANKS.find((r) => score >= r.min)!;
}
