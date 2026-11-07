from main import monthly_report, report_fukuoka, report_nagoya, report_osaka, report_tokyo


def test_東京_目標未達():
    rows = [{"branch": "tokyo", "amount": 999999}]
    assert report_tokyo(rows) == "【東京支店】\n  件数: 1件\n  合計: 999,999円\n  平均: 999,999円\n"

def test_大阪_目標ちょうど():
    rows = [{"branch": "osaka", "amount": 400000}, {"branch": "osaka", "amount": 400000}]
    assert report_osaka(rows) == "【大阪支店】\n  件数: 2件\n  合計: 800,000円\n  平均: 400,000円\n  ★目標達成★\n"

def test_名古屋_目標未達():
    rows = [{"branch": "nagoya", "amount": 499999}]
    assert report_nagoya(rows) == "【名古屋支店】\n  件数: 1件\n  合計: 499,999円\n  平均: 499,999円\n"

def test_福岡_目標未達_平均切り捨て():
    rows = [{"branch": "fukuoka", "amount": 100}, {"branch": "fukuoka", "amount": 101}]
    assert report_fukuoka(rows) == "【福岡営業所】\n  件数: 2件\n  合計: 201円\n  平均: 100円\n"

def test_東京_実績なし():
    assert report_tokyo([{"branch": "osaka", "amount": 1}]) == "【東京支店】\n  実績なし\n"

def test_月次レポート_全部入り():
    rows = [
        {"branch": "fukuoka", "amount": 5},
        {"branch": "tokyo", "amount": 7},
        {"branch": "nagoya", "amount": 600000},
    ]
    assert monthly_report(rows).startswith(
        "===== 月次レポート =====\n"
        "【東京支店】\n  件数: 1件\n  合計: 7円\n  平均: 7円\n"
        "【大阪支店】\n  実績なし\n"
        "【名古屋支店】\n  件数: 1件\n  合計: 600,000円\n  平均: 600,000円\n  ★目標達成★\n"
        "【福岡営業所】\n  件数: 1件\n  合計: 5円\n  平均: 5円\n"
    )
