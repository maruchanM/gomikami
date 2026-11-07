from main import checkout

PEN = {"name": "ボールペン", "price": 150, "qty": 2}
NOTE = {"name": "ノート", "price": 280, "qty": 3}
BAG = {"name": "かばん", "price": 4980, "qty": 1}


def test_送料込み():
    assert checkout([PEN, NOTE]) == {"subtotal": 1140, "discount": 0, "shipping": 600, "total": 1740, "message": ""}

def test_5000円以上は送料無料():
    assert checkout([BAG, PEN])["shipping"] == 0

def test_10パーセントオフ():
    assert checkout([BAG, PEN], "SALE10") == {
        "subtotal": 5280, "discount": 528, "shipping": 600, "total": 5350,
        "message": "10%OFFクーポンを適用しました",
    }

def test_500円引き():
    assert checkout([BAG], "MINUS500") == {
        "subtotal": 4980, "discount": 500, "shipping": 600, "total": 5080,
        "message": "500円引きクーポンを適用しました",
    }

def test_500円引きは3000円以上から():
    result = checkout([NOTE], "MINUS500")
    assert result["discount"] == 0
    assert result["message"] == "このクーポンは3000円以上で使えます"

def test_無効なクーポン():
    assert checkout([PEN], "TADA")["message"] == "無効なクーポンです"

def test_合計は10円未満切り捨て():
    assert checkout([{"name": "ガム", "price": 108, "qty": 1}])["total"] == 700

def test_前回の会計を引きずらない():
    checkout([BAG], "SALE10")
    assert checkout([PEN]) == {"subtotal": 300, "discount": 0, "shipping": 600, "total": 900, "message": ""}

def test_空のカート():
    assert checkout([])["total"] == 600
