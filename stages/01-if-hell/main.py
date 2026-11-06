import datetime

# 料金計算
# 2009/04 新規作成
# 2013/11 シニア対応(暫定)
# 2017/02 3D対応 ←全部の分岐に足した
def ticket_price(age, is_student, is_female, date, is_3d):
    x = 0
    flag = False
    if date.day == 1:
        flag = True
    if flag == True:
        if age < 18:
            x = 1000
            if is_3d == True:
                x = x + 400
        else:
            if age >= 60:
                x = 1200
                if is_3d == True:
                    x = x + 400
            else:
                x = 1200
                if is_3d == True:
                    x = x + 400
    else:
        if date.weekday() == 2:
            if is_female == True:
                if age < 18:
                    x = 1000
                    if is_3d == True:
                        x = x + 400
                else:
                    if age >= 60:
                        x = 1200
                        if is_3d == True:
                            x = x + 400
                    else:
                        x = 1200
                        if is_3d == True:
                            x = x + 400
            else:
                if age < 18:
                    x = 1000
                    if is_3d == True:
                        x = x + 400
                else:
                    if age >= 60:
                        x = 1200
                        if is_3d == True:
                            x = x + 400
                    else:
                        if is_student == True:
                            x = 1500
                            if is_3d == True:
                                x = x + 400
                        else:
                            x = 1900
                            if is_3d == True:
                                x = x + 400
        else:
            if age < 18:
                x = 1000
                if is_3d == True:
                    x = x + 400
            else:
                if age >= 60:
                    x = 1200
                    if is_3d == True:
                        x = x + 400
                else:
                    if is_student == True:
                        x = 1500
                        if is_3d == True:
                            x = x + 400
                    else:
                        x = 1900
                        if is_3d == True:
                            x = x + 400
    tmp = x
    return tmp
