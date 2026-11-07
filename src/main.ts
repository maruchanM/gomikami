import "@fontsource/dotgothic16";
import "./style.css";
import { escapeHtml, GameSession, type GameOutcome, mmss } from "./game";
import { PyRunner } from "./pyrunner";
import { rankOf } from "./scoring";
import { type Stage, STAGES } from "./stages";

const app = document.querySelector<HTMLElement>("#app")!;
/** 採点専用（プレイヤーのコードを実行しない） */
const judge = new PyRunner();
/** テスト実行専用。実行のたびに作り直す */
const runner = new PyRunner({ disposable: true });
const html = String.raw;

const LOGO = ` ████   ████  ██   ██ ██████ ██  ██  ████  ██   ██ ██████    ██████ ██  ██ ██████
██     ██  ██ ███ ███   ██   ██ ██  ██  ██ ███ ███   ██      ██      ████  ██
██ ███ ██  ██ ██ █ ██   ██   ████   ██████ ██ █ ██   ██      █████    ██   █████
██  ██ ██  ██ ██   ██   ██   ██ ██  ██  ██ ██   ██   ██      ██      ████  ██
 ████   ████  ██   ██ ██████ ██  ██ ██  ██ ██   ██ ██████ ██ ██████ ██  ██ ██████`;

/** █ をフォントに頼らず SVG の四角で描く（環境によって全角幅になって潰れるため） */
function logoSvg() {
  const rows = LOGO.split("\n");
  const width = Math.max(...rows.map((r) => r.length));
  const rects = rows
    .flatMap((row, y) => [...row].map((c, x) => (c === "█" ? `<rect x="${x}" y="${y * 2}" width="1.02" height="2.04"/>` : "")))
    .join("");
  return `<svg class="logo" viewBox="0 0 ${width} ${rows.length * 2}" fill="currentColor" aria-label="GOMIKAMI.EXE">${rects}</svg>`;
}

interface Best {
  score: number;
  kamido: number;
  rank: string;
}

function loadBest(stage: Stage): Best | null {
  const raw = localStorage.getItem(`gomikami.best.${stage.id}`);
  return raw ? JSON.parse(raw) : null;
}

function saveBest(stage: Stage, best: Best) {
  const prev = loadBest(stage);
  if (!prev || best.score > prev.score) localStorage.setItem(`gomikami.best.${stage.id}`, JSON.stringify(best));
  return !prev || best.score > prev.score;
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/** Enter キーかクリックを1回待つ。直前の連打で即座に進まないよう、少しの間は無視する */
function waitForEnter(el: HTMLElement, ignoreMs = 600) {
  const shownAt = performance.now();
  return new Promise<void>((resolve) => {
    const done = (e: Event) => {
      if (performance.now() - shownAt < ignoreMs) return;
      if (e instanceof KeyboardEvent) {
        if (e.ctrlKey || e.metaKey || e.altKey) return;
        if (e.key !== "Enter") return;
        e.preventDefault(); // 次の画面でフォーカスしたボタンまで押されるのを防ぐ
      }
      window.removeEventListener("keydown", done);
      el.removeEventListener("click", done);
      resolve();
    };
    window.addEventListener("keydown", done);
    el.addEventListener("click", done);
  });
}

// ---------------------------------------------------------------- 起動

async function boot() {
  app.innerHTML = `<div class="screen boot"><pre id="boot"></pre></div>`;
  const out = app.querySelector<HTMLElement>("#boot")!;
  const print = async (line: string, wait = 180) => {
    out.textContent += line + "\n";
    await sleep(wait);
  };
  await print("GOMIKAMI BIOS v0.1   (C) 2009-2026 株式会社レガシー・システムズ");
  await print("");
  await print("メモリチェック ... 640K OK  (これ以上は誰にも必要ない)");
  await print("技術的負債をスキャン ... 9,999,999 件  [警告: 上限に達しました]");
  await print("動作保証期限 ... 2011年に終了しています");
  out.textContent += "Python インタプリタをロード中 ";
  const dots = setInterval(() => (out.textContent += "."), 300);
  try {
    await Promise.all([judge.ready, runner.ready]);
    clearInterval(dots);
    await print(" OK", 400);
  } catch {
    clearInterval(dots);
    await print(" 失敗 (ネットワークを確認してください)");
    return;
  }
  const direct = stageFromUrl();
  if (direct) play(direct);
  else title();
}

/** ?stage=2 または ?stage=02-copipe-hell でタイトルを飛ばして直接始める */
function stageFromUrl() {
  const q = new URLSearchParams(location.search).get("stage");
  if (!q) return null;
  return STAGES.find((s) => s.id === q || Number(s.id.slice(0, 2)) === Number(q)) ?? null;
}

async function title() {
  app.innerHTML = html`
    <div class="screen title">
      ${logoSvg()}
      <p class="subtitle">～ ゴミコードは二度死ぬ ～</p>
      <p class="blink">PRESS ENTER</p>
      <p class="dim small">テストを壊さずに、ゴミを神にせよ。</p>
      <p class="warn small mobile-only">※ キーボード操作のゲームです。PC で遊んでください。</p>
    </div>`;
  await waitForEnter(app, 0);
  select();
}

// ---------------------------------------------------------------- ステージ選択

function select(focus = 0) {
  const rows = STAGES.map((s, i) => {
    const best = loadBest(s);
    const record = best ? `BEST ${best.score}点 [${best.rank}]` : "未クリア";
    return html`<li><button data-i="${i}"><span class="key">[${i + 1}]</span> ${s.title} <span class="dim">─ ${s.subtitle} (${mmss(s.timeLimitSec)})</span></button><span class="record${best ? "" : " dim"}">${record}</span></li>`;
  }).join("");
  const cleared = STAGES.filter((s) => loadBest(s)).length;
  app.innerHTML = html`
    <div class="screen select">
      <h2>&gt; SELECT STAGE_ <span class="dim small">クリア ${cleared}/${STAGES.length}</span></h2>
      <ul class="stage-list">${rows}<li class="dim">[?] ボス: 歴史的遺産 ─ COMING SOON (たぶん)</li></ul>
      <p class="dim small">↑↓ で選択 / Enter で開始 / 数字キーで即開始 / どのステージからでも遊べます</p>
    </div>`;
  const buttons = [...app.querySelectorAll<HTMLButtonElement>(".stage-list button")];
  buttons.forEach((b) => b.addEventListener("click", () => start(Number(b.dataset.i))));
  buttons[Math.min(focus, buttons.length - 1)]?.focus();
  const onKey = (e: KeyboardEvent) => {
    const i = buttons.indexOf(document.activeElement as HTMLButtonElement);
    if (e.key === "ArrowDown") buttons[(i + 1) % buttons.length].focus();
    else if (e.key === "ArrowUp") buttons[(i - 1 + buttons.length) % buttons.length].focus();
    else if (/^[1-9]$/.test(e.key) && Number(e.key) <= STAGES.length) start(Number(e.key) - 1);
    else return;
    e.preventDefault();
  };
  const start = (i: number) => {
    window.removeEventListener("keydown", onKey);
    play(STAGES[i]);
  };
  window.addEventListener("keydown", onKey);
}

/**
 * リザルト・ゲームオーバー後のメニュー。←→ で選んで Enter、または頭文字キー。
 * 直前の連打で即座に決定しないよう、少しの間は無視する。
 */
function afterMenu(stage: Stage, primary: "next" | "retry") {
  const index = STAGES.indexOf(stage);
  const next = STAGES[index + 1];
  const items = [
    ...(next ? [{ key: "n", label: `[N] 次へ: ${next.title}`, go: () => play(next) }] : []),
    { key: "r", label: "[R] もう一度", go: () => play(stage) },
    { key: "s", label: "[S] ステージ選択", go: () => select(index) },
  ];
  if (primary === "retry") items.unshift(...items.splice(items.findIndex((it) => it.key === "r"), 1));
  const box = app.querySelector<HTMLElement>(".after-menu")!;
  box.innerHTML = items.map((it, i) => html`<button data-i="${i}">${escapeHtml(it.label)}</button>`).join("");
  const buttons = [...box.querySelectorAll<HTMLButtonElement>("button")];
  const shownAt = performance.now();
  let done = false;
  const choose = (i: number) => {
    if (done || performance.now() - shownAt < 600) return;
    done = true;
    window.removeEventListener("keydown", onKey);
    document.body.classList.remove("flash-red");
    items[i].go();
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const i = buttons.indexOf(document.activeElement as HTMLButtonElement);
    const byKey = items.findIndex((it) => it.key === e.key.toLowerCase());
    if (e.key === "ArrowRight" || e.key === "ArrowDown") buttons[(i + 1) % buttons.length].focus();
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") buttons[(i - 1 + buttons.length) % buttons.length].focus();
    else if (e.key === "Enter") choose(Math.max(i, 0));
    else if (byKey >= 0) choose(byKey);
    else return;
    e.preventDefault();
  };
  buttons.forEach((b, i) => b.addEventListener("click", () => choose(i)));
  buttons[0].focus();
  window.addEventListener("keydown", onKey);
}

// ---------------------------------------------------------------- プレイ

function play(stage: Stage) {
  const session = new GameSession(app, stage, judge, runner, (outcome) => result(outcome));
  void session.start();
}

function result(outcome: GameOutcome) {
  if (outcome.kind === "quit") return select();
  if (outcome.kind === "gameover") {
    document.body.classList.add("flash-red");
    app.innerHTML = html`
      <div class="screen gameover">
        <pre class="big err">*** GAME OVER ***</pre>
        <p class="big-sub err">${escapeHtml(outcome.title)}</p>
        <p>${escapeHtml(outcome.reason)}</p>
        <p class="dim">STAGE ${outcome.stage.id.slice(0, 2)}: ${outcome.stage.title}</p>
        <div class="after-menu"></div>
      </div>`;
    return afterMenu(outcome.stage, "retry");
  }

  const rank = rankOf(outcome.kamido);
  const score = outcome.kamido * 10 + outcome.remainingSec + outcome.hp;
  const isNew = saveBest(outcome.stage, { score, kamido: outcome.kamido, rank: rank.name });
  const rows = outcome.parts
    .map((p) => {
      const mark = p.score === null ? "─" : p.score >= 1 ? "◎" : p.score > 0.5 ? "○" : p.score > 0 ? "△" : "×";
      return html`<tr><td>${mark}</td><td>${p.label}</td><td class="num">${p.original}</td><td>→</td><td class="num">${p.current}</td><td class="num dim">(目標 ${p.target})</td></tr>`;
    })
    .join("");
  app.innerHTML = html`
    <div class="screen result">
      <h2>&gt; REVIEW RESULT_</h2>
      <div class="rank-box rank-${rank.name}">
        <div class="dim small">ランク</div>
        <div class="rank">${rank.name}</div>
        <div>「${rank.comment}」</div>
      </div>
      <table class="metrics">${rows}</table>
      <pre class="score">神度     ${String(outcome.kamido).padStart(5)} × 10
残り時間 ${String(outcome.remainingSec).padStart(5)} 秒
信用度   ${String(outcome.hp).padStart(5)}
─────────────────
SCORE    ${String(score).padStart(5)}${isNew ? "  ★NEW RECORD★" : ""}</pre>
      <div class="after-menu"></div>
    </div>`;
  afterMenu(outcome.stage, "next");
}

void boot();
