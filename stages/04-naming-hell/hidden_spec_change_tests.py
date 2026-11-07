from main import honor_students


def test_丸めて90なら優秀者():
    assert honor_students([("y", [89.95])]) == ["y"]

def test_同点は元の順():
    assert honor_students([("b", [95]), ("a", [95]), ("c", [99])]) == ["c", "b", "a"]

def test_空():
    assert honor_students([]) == []
