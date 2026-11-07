FREE_SHIPPING_FROM = 5000
SHIPPING_FEE = 600
MINUS500_MINIMUM = 3000
MINUS500_AMOUNT = 500
SALE10_PERCENT = 10


def subtotal_of(cart_items):
    return sum(item["price"] * item["qty"] for item in cart_items)


def discount_for(coupon_code, subtotal):
    """(値引き額, メッセージ) を返す。"""
    if coupon_code == "":
        return 0, ""
    if coupon_code == "SALE10":
        return subtotal * SALE10_PERCENT // 100, "10%OFFクーポンを適用しました"
    if coupon_code == "MINUS500":
        if subtotal < MINUS500_MINIMUM:
            return 0, "このクーポンは3000円以上で使えます"
        return MINUS500_AMOUNT, "500円引きクーポンを適用しました"
    return 0, "無効なクーポンです"


def shipping_for(amount, member):
    return 0 if member or amount >= FREE_SHIPPING_FROM else SHIPPING_FEE


def round_down_to_ten(amount):
    return amount // 10 * 10


def checkout(cart_items, coupon_code="", member=False):
    subtotal = subtotal_of(cart_items)
    discount, message = discount_for(coupon_code, subtotal)
    shipping = shipping_for(subtotal - discount, member)
    total = round_down_to_ten(subtotal - discount + shipping)
    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "total": total,
        "message": message,
    }
