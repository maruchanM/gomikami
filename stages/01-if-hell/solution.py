ADULT_AGE = 18
SENIOR_AGE = 60

REGULAR_PRICE = 1900
STUDENT_PRICE = 1500
CHILD_PRICE = 1000
SENIOR_PRICE = 1200
DISCOUNT_PRICE = 1200
SURCHARGE_3D = 400

WEDNESDAY = 2
MOVIE_DAY = 1


def base_price(age, is_student):
    if age < ADULT_AGE:
        return CHILD_PRICE
    if age >= SENIOR_AGE:
        return SENIOR_PRICE
    if is_student:
        return STUDENT_PRICE
    return REGULAR_PRICE


def is_discount_day(date, is_female):
    return date.day == MOVIE_DAY or (date.weekday() == WEDNESDAY and is_female)


def ticket_price(age, is_student, is_female, date, is_3d):
    price = base_price(age, is_student)
    if is_discount_day(date, is_female):
        price = min(price, DISCOUNT_PRICE)
    if is_3d:
        price += SURCHARGE_3D
    return price
