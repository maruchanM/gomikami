from main import monthly_report, report_sapporo


def test_札幌支店():
    rows = [{"branch": "sapporo", "amount": 200000}, {"branch": "sapporo", "amount": 50000}]
    assert report_sapporo(rows) == "【札幌支店】\n  件数: 2件\n  合計: 250,000円\n  平均: 125,000円\n  ★目標達成★\n"

def test_札幌_目標未達():
    assert report_sapporo([{"branch": "sapporo", "amount": 249999}]).endswith("平均: 249,999円\n")

def test_月次レポートの最後に札幌():
    rows = [{"branch": "sapporo", "amount": 1}]
    assert monthly_report(rows).endswith("【福岡営業所】\n  実績なし\n【札幌支店】\n  件数: 1件\n  合計: 1円\n  平均: 1円\n")

def test_空なら5拠点が実績なし():
    assert monthly_report([]).count("実績なし") == 5
