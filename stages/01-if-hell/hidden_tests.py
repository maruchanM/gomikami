# 抜き打ち検査（画面には期待値を出さない。テストの答えの丸暗記対策）
from datetime import date
from main import ticket_price

MON = date(2026, 11, 9)
WED = date(2026, 11, 11)
FIRST = date(2027, 1, 1)


def test_1():
    assert ticket_price(65, False, True, WED, False) == 1200

def test_2():
    assert ticket_price(21, True, True, WED, False) == 1200

def test_3():
    assert ticket_price(22, True, False, FIRST, True) == 1600

def test_4():
    assert ticket_price(8, False, False, MON, True) == 1400

def test_5():
    assert ticket_price(59, False, False, MON, False) == 1900

def test_6():
    assert ticket_price(18, True, False, MON, False) == 1500

def test_7():
    assert ticket_price(70, False, False, MON, True) == 1600

def test_8():
    assert ticket_price(25, True, False, WED, True) == 1900
