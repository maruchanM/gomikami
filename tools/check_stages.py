"""全ステージの整合性チェック（CPython で実行）。

- 初期コードは公開テストに通る / 仕様変更テストには落ちる
- 模範解答は該当するテストに全部通る
- 初期コードと模範解答の指標を表示し、模範解答の指標を targets.json に書き出す
  （ブラウザには模範解答そのものは配信せず、targets.json だけを渡す）
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "python"))
import harness  # noqa: E402


def load(stage_dir, name):
    return (stage_dir / name).read_text(encoding="utf-8")


def run(stage_dir, main_src, test_names):
    tests = {name: load(stage_dir, name) for name in test_names}
    with tempfile.TemporaryDirectory() as tmp:
        return harness.run_tests(tmp, {"main.py": main_src}, tests)


def expect(label, results, should_pass):
    failed = [r for r in results if not r["ok"]]
    ok = (not failed) if should_pass else bool(failed)
    print(f"  [{'OK' if ok else 'NG'}] {label}: {len(results) - len(failed)}/{len(results)} 通過")
    if ok is False and should_pass:
        for r in failed:
            print(f"      - {r['name']}: {r['message']}")
    return ok


def main():
    all_ok = True
    for stage_dir in sorted(p for p in (ROOT / "stages").iterdir() if p.is_dir()):
        stage = json.loads(load(stage_dir, "stage.json"))
        print(f"== {stage_dir.name}: {stage['title']}")
        original = load(stage_dir, "main.py")
        base = ["tests.py", *([stage["hiddenTests"]] if "hiddenTests" in stage else [])]
        all_ok &= expect("初期コード × 公開/隠しテスト", run(stage_dir, original, base), True)
        all_ok &= expect("模範解答 × 公開/隠しテスト", run(stage_dir, load(stage_dir, "solution.py"), base), True)
        solutions = {"solution.py": base}
        for event in stage.get("events", []):
            if event["type"] == "spec_change":
                all_ok &= expect("初期コード × 仕様変更テスト(落ちるべき)", run(stage_dir, original, [event["tests"]]), False)
                if "solution" in event:
                    names = [*base, event["tests"], *([event["hiddenTests"]] if "hiddenTests" in event else [])]
                    solutions[event["solution"]] = names
                    all_ok &= expect(f"{event['solution']} × 全テスト", run(stage_dir, load(stage_dir, event["solution"]), names), True)
        print(f"  初期コード: {harness.analyze(original)['metrics']}")
        targets = {}
        for name in [*solutions, "main.py"]:
            analysis = harness.analyze(load(stage_dir, name))
            if analysis["audit"]:
                print(f"  [NG] {name} が監査に引っかかる: {analysis['audit']}")
                all_ok = False
            if name != "main.py":
                targets[name] = analysis["metrics"]
                print(f"  {name}: {analysis['metrics']}")
        (stage_dir / "targets.json").write_text(json.dumps(targets, indent=2) + "\n", encoding="utf-8")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
