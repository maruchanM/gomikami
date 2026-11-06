from datetime import date
from main import ticket_price

TUE = date(2026, 11, 10)


def test_レイトショーは1400円():
    assert ticket_price(30, False, False, TUE, False, start_hour=20) == 1400

def test_レイトショー_19時開始は対象外():
    assert ticket_price(30, False, False, TUE, False, start_hour=19) == 1900

def test_レイトショー_子どもは1000円のまま():
    assert ticket_price(10, False, False, TUE, False, start_hour=21) == 1000

def test_レイトショー_3D():
    assert ticket_price(30, False, False, TUE, True, start_hour=21) == 1800

def test_開始時刻を省略したら今まで通り():
    assert ticket_price(30, False, False, TUE, False) == 1900
