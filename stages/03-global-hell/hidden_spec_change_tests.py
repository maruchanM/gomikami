from main import checkout


def test_会員_空のカートは0円():
    assert checkout([], member=True)["total"] == 0

def test_会員_切り捨て():
    assert checkout([{"name": "x", "price": 1234, "qty": 1}], "", True)["total"] == 1230

def test_会員_無効クーポン():
    result = checkout([{"name": "x", "price": 100, "qty": 1}], "NOPE", member=True)
    assert (result["shipping"], result["message"]) == (0, "無効なクーポンです")
