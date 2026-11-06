import type { Metrics } from "./scoring";

const pick = <T>(xs: T[]) => xs[Math.floor(Math.random() * xs.length)];

/** ALL GREEN の時のレビュアーの一言。一番ひどい箇所をいじる */
export function quipFor(m: Metrics, badNames: string[], kamido: number, before: number): string {
  const problems: [boolean, string][] = [
    [m.tricks > 0, `小細工${m.tricks}箇所。数式で分岐を隠すな。それは暗号です。`],
    [m.nesting >= 5, `ネスト${m.nesting}段…マトリョーシカかな？`],
    [m.duplication >= 20, `コピペ${m.duplication}行。Ctrl+V キーが摩耗しています。`],
    [m.complexity >= 15, `複雑度${m.complexity}。分岐の数だけ並行世界があります。`],
    [m.length >= 40, `関数${m.length}行。スクロールしすぎて腱鞘炎になりました。`],
    [m.magic >= 10, `マジックナンバー${m.magic}個。数秘術の儀式ですか？`],
    [badNames.length > 0, `${badNames.slice(0, 3).join(", ")} …暗号資産の秘密鍵？`],
    [m.longlines > 0, `横に長い行が${m.longlines}本。ワイドモニター前提ですか？`],
    [m.globals > 0, `グローバル変数${m.globals}個。みんなの共有財産（誰も責任を取らない）`],
  ];
  const worst = problems.find(([hit]) => hit);
  const delta = kamido - before;
  const progress = delta > 0 ? `神度 +${delta}。` : delta < 0 ? `神度 ${delta}。悪化してませんか？` : "";
  if (worst) return progress + worst[1];
  if (kamido >= 90) return progress + pick(["…LGTM。（悔しそう）", "文句のつけようがない。つまらん。", "これ、本当にあなたが書きました？"]);
  return progress + pick(["まあ…読める。", "可もなく不可もなく。", "インデントはタブ派なんですけどね。"]);
}

/** 信用度が減った時の一言 */
export function damageQuip(hp: number): string {
  if (hp <= 0) return "Slack に #炎上対策 チャンネルが作られました。";
  if (hp <= 30) return pick(["部長が後ろに立っています。", "人事から面談のお誘いが届きました。", "あなたの席の観葉植物が枯れ始めました。"]);
  return pick([
    "部長が見ています。",
    "CI が真っ赤です。",
    "隣の席の先輩がため息をつきました。",
    "git blame にあなたの名前が刻まれました。",
    "本番じゃなくてよかったですね。",
  ]);
}
