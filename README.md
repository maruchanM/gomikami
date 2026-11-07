# GOMIKAMI.EXE ～ゴミコードは二度死ぬ～

テストは通るけど読めたもんじゃない Python のゴミコードを、テストを壊さずに神コードへ書き直すクソゲー。
ブラウザだけで動く（Python は Pyodide で実行）。仕様は [SPEC.md](SPEC.md)。

## 遊び方（ローカル）

```sh
npm install
npm run dev        # http://localhost:5173/
```

- 公開版: https://maruchanm.github.io/gomikami/
- `?stage=2` を URL に付けるとタイトルを飛ばしてそのステージから始まる
- ステージ選択は数字キーで即開始。クリア後は Enter で次のステージ、R でもう一度、S でステージ選択
- `?speed=20` を URL に付けるとゲーム内時間が20倍速になる（デバッグ用）
- 公開版は `main` に push すると GitHub Actions がビルドして GitHub Pages に出す（`.github/workflows/deploy.yml`）

## ステージ

| # | 名前 | 題材 | 主な臭い | 仕様変更 |
|---|---|---|---|---|
| 1 | if地獄 | 映画館の料金計算 | ネスト7段、マジックナンバー | レイトショー割 |
| 2 | コピペ地獄 | 支店別の月次レポート | ほぼ同じ関数×4 | 札幌支店の追加 |
| 3 | グローバル地獄 | ショッピングカートの会計 | グローバル変数で関数間の受け渡し、「触るな」コメント | 会員は送料無料 |
| 4 | 命名地獄 | クラスの成績集計 | `f`/`g`/`l`/`O`、`list`/`sum` の上書き | 優秀者の表彰 |

## ディレクトリ構成

| パス | 内容 |
|---|---|
| `src/main.ts` | 画面遷移（起動・タイトル・ステージ選択・リザルト） |
| `src/game.ts` | ゲーム本体（HUD・タイマー・信用度・イベント・提出） |
| `src/quips.ts` | 毒舌レビュアーのセリフ |
| `src/scoring.ts` | 神度の計算とランク |
| `src/editor.ts` | CodeMirror の設定（Undo 回数制限つき） |
| `src/pyrunner.ts`, `src/py.worker.ts` | Pyodide を載せた Web Worker（採点用とテスト実行用の2つ） |
| `src/python/harness.py` | テスト実行・採点指標・監査（CPython でも動く） |
| `stages/NN-name/` | ステージ1つ分（下記） |
| `tools/check_stages.py` | ステージの整合性チェックと `targets.json` の生成（build/dev 時に自動実行） |

## ステージの追加

`stages/02-xxx/` を作って以下を置き、`npm run check-stages` が全部 OK になればゲームに出る。

| ファイル | 内容 |
|---|---|
| `stage.json` | タイトル・チケット文・制限時間・Undo 上限・イベント |
| `main.py` | ゴミコード（初期状態。`tests.py` は全部通ること） |
| `tests.py` | 公開テスト（`test_` で始まる関数、`assert a == b` 推奨） |
| `spec_change_tests.py` | 仕様変更イベントで追加されるテスト（任意） |
| `solution*.py` | 模範解答。目標値の算出にだけ使い、ブラウザには配信しない |
| `targets.json` | 自動生成（模範解答の指標） |
