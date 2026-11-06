# 抜き打ち検査（仕様変更後）
from datetime import date
from main import ticket_price

MON = date(2026, 11, 9)
WED = date(2026, 11, 11)
FIRST = date(2027, 1, 1)


def test_1():
    assert ticket_price(65, False, False, MON, False, start_hour=21) == 1200

def test_2():
    assert ticket_price(20, True, False, MON, False, start_hour=22) == 1400

def test_3():
    assert ticket_price(40, False, False, FIRST, False, start_hour=21) == 1200

def test_4():
    assert ticket_price(33, False, True, WED, True, start_hour=20) == 1600

def test_5():
    assert ticket_price(45, False, False, MON, True, start_hour=23) == 1800

def test_6():
    assert ticket_price(45, False, False, MON, False, start_hour=0) == 1900
