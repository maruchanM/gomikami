from main import grade_report, passed_count

CLASS = [
    ("佐藤", [92, 88, 95]),
    ("鈴木", [55, 60, 58]),
    ("高橋", [70, 81, 79]),
    ("田中", [100, 100, 100]),
]


def test_順位表():
    assert grade_report(CLASS) == [
        "1位 田中: 100.0点 S",
        "2位 佐藤: 91.7点 S",
        "3位 高橋: 76.7点 B",
        "4位 鈴木: 57.7点 D",
    ]

def test_合格者数():
    assert passed_count(CLASS) == 3

def test_同点は元の順番():
    assert grade_report([("A", [80]), ("B", [80])]) == ["1位 A: 80.0点 A", "2位 B: 80.0点 A"]

def test_評価の境目():
    rows = grade_report([("X", [60]), ("Y", [59.9])])
    assert rows == ["1位 X: 60.0点 C", "2位 Y: 59.9点 D"]

def test_空のクラス():
    assert grade_report([]) == []
    assert passed_count([]) == 0
