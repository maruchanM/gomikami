# 月次レポート
# 2015/04 東京のを作った
# 2015/05 大阪 (東京のをコピー)
# 2016/10 名古屋 (大阪のをコピー)
# 2019/01 福岡 (どれかをコピー。どれだったかは忘れた)

def report_tokyo(rows):
    total = 0
    count = 0
    for r in rows:
        if r["branch"] == "tokyo":
            total = total + r["amount"]
            count = count + 1
    if count == 0:
        return "【東京支店】\n  実績なし\n"
    avg = total // count
    s = "【東京支店】\n"
    s = s + "  件数: " + str(count) + "件\n"
    s = s + "  合計: " + format(total, ",") + "円\n"
    s = s + "  平均: " + format(avg, ",") + "円\n"
    if total >= 1000000:
        s = s + "  ★目標達成★\n"
    return s


def report_osaka(rows):
    total = 0
    count = 0
    for r in rows:
        if r["branch"] == "osaka":
            total = total + r["amount"]
            count = count + 1
    if count == 0:
        return "【大阪支店】\n  実績なし\n"
    avg = total // count
    s = "【大阪支店】\n"
    s = s + "  件数: " + str(count) + "件\n"
    s = s + "  合計: " + format(total, ",") + "円\n"
    s = s + "  平均: " + format(avg, ",") + "円\n"
    if total >= 800000:
        s = s + "  ★目標達成★\n"
    return s


def report_nagoya(rows):
    total = 0
    count = 0
    for r in rows:
        if r["branch"] == "nagoya":
            total = total + r["amount"]
            count = count + 1
    if count == 0:
        return "【名古屋支店】\n  実績なし\n"
    avg = total // count
    s = "【名古屋支店】\n"
    s = s + "  件数: " + str(count) + "件\n"
    s = s + "  合計: " + format(total, ",") + "円\n"
    s = s + "  平均: " + format(avg, ",") + "円\n"
    if total >= 500000:
        s = s + "  ★目標達成★\n"
    return s


def report_fukuoka(rows):
    total = 0
    count = 0
    for r in rows:
        if r["branch"] == "fukuoka":
            total = total + r["amount"]
            count = count + 1
    if count == 0:
        return "【福岡営業所】\n  実績なし\n"
    avg = total // count
    s = "【福岡営業所】\n"
    s = s + "  件数: " + str(count) + "件\n"
    s = s + "  合計: " + format(total, ",") + "円\n"
    s = s + "  平均: " + format(avg, ",") + "円\n"
    if total >= 300000:
        s = s + "  ★目標達成★\n"
    return s


def monthly_report(rows):
    s = "===== 月次レポート =====\n"
    s = s + report_tokyo(rows)
    s = s + report_osaka(rows)
    s = s + report_nagoya(rows)
    s = s + report_fukuoka(rows)
    return s
