from main import grade_report, honor_students

CLASS = [
    ("佐藤", [92, 88, 95]),
    ("鈴木", [55, 60, 58]),
    ("田中", [100, 100, 100]),
]


def test_優秀者():
    assert honor_students(CLASS) == ["田中", "佐藤"]

def test_順位表は変わらない():
    assert grade_report(CLASS)[0] == "1位 田中: 100.0点 S"

def test_優秀者なし():
    assert honor_students([("x", [89.94])]) == []
