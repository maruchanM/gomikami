from main import monthly_report, report_sapporo, report_tokyo


def test_札幌_目標ちょうど():
    assert "★目標達成★" in report_sapporo([{"branch": "sapporo", "amount": 250000}])

def test_札幌_実績なし():
    assert report_sapporo([]) == "【札幌支店】\n  実績なし\n"

def test_既存拠点は変わらない():
    rows = [{"branch": "tokyo", "amount": 1000000}]
    assert report_tokyo(rows) == "【東京支店】\n  件数: 1件\n  合計: 1,000,000円\n  平均: 1,000,000円\n  ★目標達成★\n"

def test_札幌_平均切り捨て():
    rows = [{"branch": "sapporo", "amount": 10}, {"branch": "sapporo", "amount": 11}, {"branch": "sapporo", "amount": 11}]
    assert "平均: 10円" in monthly_report(rows)
