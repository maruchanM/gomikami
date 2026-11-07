# 成績集計
# 作者: 前任者 (退職済み)。変数名は「打つのが速い」を最優先に決めたそうです


def f(a):
    if a >= 90:
        return "S"
    if a >= 80:
        return "A"
    if a >= 70:
        return "B"
    if a >= 60:
        return "C"
    return "D"


def g(l):
    sum = 0
    for x in l:
        sum = sum + x
    return sum / len(l)


def grade_report(data):
    list = []
    for d in data:
        O = d[0]
        l = d[1]
        a2 = g(l)
        a2 = round(a2, 1)
        b = f(a2)
        tmp = O + ": " + str(a2) + "点 " + b
        list.append((a2, tmp))
    list.sort(key=lambda z: -z[0])
    res = []
    for i in range(len(list)):
        res.append(str(i + 1) + "位 " + list[i][1])
    return res


def h(data):
    c = 0
    for d in data:
        if f(round(g(d[1]), 1)) == "D":
            c = c + 1
    return c


def passed_count(data):
    return len(data) - h(data)
