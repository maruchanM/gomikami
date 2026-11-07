from main import checkout

BAG = {"name": "かばん", "price": 4980, "qty": 1}


def test_会員は送料無料():
    assert checkout([BAG], member=True)["shipping"] == 0

def test_会員でもクーポンは使える():
    assert checkout([BAG], "MINUS500", member=True) == {
        "subtotal": 4980, "discount": 500, "shipping": 0, "total": 4480,
        "message": "500円引きクーポンを適用しました",
    }

def test_非会員は今まで通り():
    assert checkout([BAG], member=False)["shipping"] == 600
