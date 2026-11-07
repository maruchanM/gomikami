from main import checkout


def test_ちょうど5000円():
    assert checkout([{"name": "x", "price": 2500, "qty": 2}])["shipping"] == 0

def test_割引後に5000円を下回ると送料():
    result = checkout([{"name": "x", "price": 5400, "qty": 1}], "SALE10")
    assert result == {"subtotal": 5400, "discount": 540, "shipping": 600, "total": 5460, "message": "10%OFFクーポンを適用しました"}

def test_10パーセントは切り捨て():
    assert checkout([{"name": "x", "price": 999, "qty": 1}], "SALE10")["discount"] == 99

def test_500円引き_ちょうど3000円():
    result = checkout([{"name": "x", "price": 1000, "qty": 3}], "MINUS500")
    assert (result["discount"], result["total"]) == (500, 3100)

def test_切り捨て_割引あり():
    assert checkout([{"name": "x", "price": 777, "qty": 7}], "MINUS500")["total"] == 5530

def test_無効クーポンでも計算はする():
    assert checkout([{"name": "x", "price": 6000, "qty": 1}], "sale10") == {
        "subtotal": 6000, "discount": 0, "shipping": 0, "total": 6000, "message": "無効なクーポンです",
    }

def test_呼び出し後もカートを書き換えない():
    cart = [{"name": "x", "price": 100, "qty": 1}]
    checkout(cart, "SALE10")
    assert cart == [{"name": "x", "price": 100, "qty": 1}]
