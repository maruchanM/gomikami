from datetime import date
from main import ticket_price

TUE = date(2026, 11, 10)   # ふつうの火曜
WED = date(2026, 11, 11)   # 水曜（レディースデイ）
FIRST = date(2026, 12, 1)  # 映画の日（1日）


def test_一般():
    assert ticket_price(30, False, False, TUE, False) == 1900

def test_大学生():
    assert ticket_price(20, True, False, TUE, False) == 1500

def test_高校生以下():
    assert ticket_price(17, True, False, TUE, False) == 1000

def test_シニア():
    assert ticket_price(60, False, False, TUE, False) == 1200

def test_3Dは400円増し():
    assert ticket_price(30, False, False, TUE, True) == 2300

def test_レディースデイ_女性は1200円():
    assert ticket_price(30, False, True, WED, False) == 1200

def test_レディースデイ_男性は通常料金():
    assert ticket_price(30, False, False, WED, False) == 1900

def test_レディースデイ_子どもは1000円のまま():
    assert ticket_price(10, False, True, WED, False) == 1000

def test_映画の日は1200円():
    assert ticket_price(20, True, False, FIRST, False) == 1200

def test_映画の日_子どもは1000円のまま():
    assert ticket_price(10, False, False, FIRST, False) == 1000

def test_映画の日_3D():
    assert ticket_price(40, False, False, FIRST, True) == 1600
