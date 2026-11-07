from main import grade_report, passed_count


def test_全評価():
    rows = grade_report([("a", [90]), ("b", [89.96]), ("c", [70]), ("d", [69]), ("e", [0])])
    assert rows == ["1位 a: 90.0点 S", "2位 b: 90.0点 S", "3位 c: 70.0点 B", "4位 d: 69.0点 C", "5位 e: 0.0点 D"]

def test_丸めてから評価する():
    assert grade_report([("p", [79.96])]) == ["1位 p: 80.0点 A"]

def test_不合格は丸めた点で判定():
    assert passed_count([("q", [59.96]), ("r", [59.94])]) == 1

def test_平均():
    assert grade_report([("s", [1, 2])]) == ["1位 s: 1.5点 D"]

def test_元のリストを壊さない():
    data = [("t", [10, 20])]
    grade_report(data)
    assert data == [("t", [10, 20])]
