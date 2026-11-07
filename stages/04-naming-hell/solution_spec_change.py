# 成績集計
GRADE_BORDERS = [(90, "S"), (80, "A"), (70, "B"), (60, "C")]
FAILING_GRADE = "D"
HONOR_GRADE = "S"


def letter_grade(score):
    for border, grade in GRADE_BORDERS:
        if score >= border:
            return grade
    return FAILING_GRADE


def average_score(scores):
    return round(sum(scores) / len(scores), 1)


def ranked(students):
    """(名前, 平均点) を平均点の高い順に。同点は元の順。"""
    averages = [(name, average_score(scores)) for name, scores in students]
    return sorted(averages, key=lambda entry: -average_of(entry))


def average_of(entry):
    _, average = entry
    return average


def grade_report(students):
    return [
        f"{place}位 {name}: {average}点 {letter_grade(average)}"
        for place, (name, average) in enumerate(ranked(students), start=1)
    ]


def passed_count(students):
    return sum(1 for _, average in ranked(students) if letter_grade(average) != FAILING_GRADE)


def honor_students(students):
    return [name for name, average in ranked(students) if letter_grade(average) == HONOR_GRADE]
