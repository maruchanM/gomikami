from main import monthly_report, report_fukuoka, report_nagoya, report_osaka, report_tokyo

ROWS = [
    {"branch": "tokyo", "amount": 600000},
    {"branch": "tokyo", "amount": 450000},
    {"branch": "osaka", "amount": 300000},
    {"branch": "osaka", "amount": 200001},
    {"branch": "osaka", "amount": 10000},
    {"branch": "nagoya", "amount": 500000},
    {"branch": "kyoto", "amount": 999999},
]


def test_東京():
    assert report_tokyo(ROWS) == "【東京支店】\n  件数: 2件\n  合計: 1,050,000円\n  平均: 525,000円\n  ★目標達成★\n"

def test_大阪_平均は切り捨て():
    assert report_osaka(ROWS) == "【大阪支店】\n  件数: 3件\n  合計: 510,001円\n  平均: 170,000円\n"

def test_名古屋_目標ちょうどで達成():
    assert report_nagoya(ROWS) == "【名古屋支店】\n  件数: 1件\n  合計: 500,000円\n  平均: 500,000円\n  ★目標達成★\n"

def test_福岡_実績なし():
    assert report_fukuoka(ROWS) == "【福岡営業所】\n  実績なし\n"

def test_福岡は営業所():
    rows = [{"branch": "fukuoka", "amount": 300000}]
    assert report_fukuoka(rows) == "【福岡営業所】\n  件数: 1件\n  合計: 300,000円\n  平均: 300,000円\n  ★目標達成★\n"

def test_月次レポートは4拠点を順に並べる():
    expected = (
        "===== 月次レポート =====\n"
        + report_tokyo(ROWS) + report_osaka(ROWS) + report_nagoya(ROWS) + report_fukuoka(ROWS)
    )
    assert monthly_report(ROWS).startswith(expected)

def test_空でも全拠点が実績なし():
    expected = "===== 月次レポート =====\n" + "".join(
        f"【{name}】\n  実績なし\n" for name in ["東京支店", "大阪支店", "名古屋支店", "福岡営業所"]
    )
    assert monthly_report([]).startswith(expected)
