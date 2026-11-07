# ショッピングカートの会計
# 関数同士はグローバル変数で会話します（引数を書くのが面倒だったので）

items = []
coupon = ""
subtotal = 0
discount = 0
shipping = 0
total = 0
msg = ""


def calc_subtotal():
    global subtotal
    subtotal = 0
    for it in items:
        subtotal = subtotal + it["price"] * it["qty"]


def calc_discount():
    global discount, msg
    discount = 0
    if coupon == "":
        return
    if coupon == "SALE10":
        discount = subtotal * 10 // 100
        msg = "10%OFFクーポンを適用しました"
    elif coupon == "MINUS500":
        if subtotal >= 3000:
            discount = 500
            msg = "500円引きクーポンを適用しました"
        else:
            msg = "このクーポンは3000円以上で使えます"
    else:
        msg = "無効なクーポンです"


def calc_shipping():
    global shipping
    if subtotal - discount >= 5000:
        shipping = 0
    else:
        shipping = 600


def calc_total():
    global total
    total = subtotal - discount + shipping
    # 触るな。動いてる理由は誰も知らない
    total = total // 10 * 10


def checkout(cart_items, coupon_code=""):
    global items, coupon, msg
    items = cart_items
    coupon = coupon_code
    msg = ""
    calc_subtotal()
    calc_discount()
    calc_shipping()
    calc_total()
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping, "total": total, "message": msg}
