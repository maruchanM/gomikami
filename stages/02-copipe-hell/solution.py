from dataclasses import dataclass


@dataclass(frozen=True)
class Branch:
    code: str
    label: str
    goal: int


BRANCHES = [
    Branch("tokyo", "東京支店", 1_000_000),
    Branch("osaka", "大阪支店", 800_000),
    Branch("nagoya", "名古屋支店", 500_000),
    Branch("fukuoka", "福岡営業所", 300_000),
]
BY_CODE = {branch.code: branch for branch in BRANCHES}


def branch_report(rows, branch):
    amounts = [row["amount"] for row in rows if row["branch"] == branch.code]
    lines = [f"【{branch.label}】"]
    if not amounts:
        lines.append("  実績なし")
    else:
        total = sum(amounts)
        lines.append(f"  件数: {len(amounts)}件")
        lines.append(f"  合計: {total:,}円")
        lines.append(f"  平均: {total // len(amounts):,}円")
        if total >= branch.goal:
            lines.append("  ★目標達成★")
    return "\n".join(lines) + "\n"


def report_tokyo(rows):
    return branch_report(rows, BY_CODE["tokyo"])


def report_osaka(rows):
    return branch_report(rows, BY_CODE["osaka"])


def report_nagoya(rows):
    return branch_report(rows, BY_CODE["nagoya"])


def report_fukuoka(rows):
    return branch_report(rows, BY_CODE["fukuoka"])


def monthly_report(rows):
    return "===== 月次レポート =====\n" + "".join(branch_report(rows, branch) for branch in BRANCHES)
