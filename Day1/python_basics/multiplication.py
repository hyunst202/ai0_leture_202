"""print와 반복문을 이용한 구구단 실습."""


def practice_printing():
    """print로 구구단 일부를 직접 출력합니다."""
    print("2 x 1 = 2")
    print("2 x 2 = 4")
    print("2 x 3 = 6")
    print("2 x 4 = 8")


def practice_nested_loops():
    """중첩 반복문과 f-string으로 구구단 표를 출력합니다."""
    for dan in range(2, 5):
        for number in range(1, 5):
            print(f"{dan} x {number} = {dan * number}", end="\t")
        print()

    print("=" * 60)

    for multiplier in range(1, 5):
        for dan in range(2, 10):
            print(f"{dan} x {multiplier} = {dan * multiplier}", end="\t")
        print()
