# Python 기초 실습 모음
# 실행 방법: python python_basics_practice.py
# 각 실습 함수의 주석을 확인하고, 아래 main()에서 원하는 실습을 실행하세요.

import random


def practice_variables_and_math():
    """1. 변수와 사칙연산"""
    number1 = 100
    number2 = 200

    print("number1 + number2 =", number1 + number2)
    print("number1 - number2 =", number1 - number2)
    print("number1 * number2 =", number1 * number2)
    print("number1 / number2 =", number1 / number2)


def practice_printing():
    """2. print로 구구단 한 줄 출력하기"""
    print("2 x 1 = 2")
    print("2 x 2 = 4")
    print("2 x 3 = 6")
    print("2 x 4 = 8")


def practice_nested_loops():
    """3. 중첩 반복문과 f-string으로 구구단 표 만들기"""
    # 2단부터 4단까지, 각 단을 1~4까지 출력
    for dan in range(2, 5):
        for number in range(1, 5):
            print(f"{dan} x {number} = {dan * number}", end="\t")
        print()  # 다음 줄로 이동

    print("=" * 60)

    # 1~4를 곱하는 구구단 표 (2단부터 9단까지)
    for multiplier in range(1, 5):
        for dan in range(2, 10):
            print(f"{dan} x {multiplier} = {dan * multiplier}", end="\t")
        print()


def number_guessing_game():
    """4. 숫자 맞히기 게임: 입력, 조건문, 반복문, random 사용"""
    answer = random.randint(1, 100)
    attempts = 0

    print("1부터 100 사이의 숫자를 맞혀 보세요!")
    while True:
        try:
            guess = int(input("숫자 입력: "))
        except ValueError:
            print("숫자로 입력해 주세요.")
            continue

        if not 1 <= guess <= 100:
            print("1부터 100 사이로 입력해 주세요.")
            continue

        attempts += 1
        if guess > answer:
            print("정답은 입력한 숫자보다 작습니다.")
        elif guess < answer:
            print("정답은 입력한 숫자보다 큽니다.")
        else:
            print(f"정답입니다! {attempts}번 만에 맞혔어요.")
            break


def practice_exercises():
    """5. 직접 풀어보기 (아래 안내를 보고 코드를 작성해 보세요)"""
    # 연습 1: 두 수를 입력받아 합계와 평균을 출력해 보세요.
    # 연습 2: 원하는 숫자의 단을 입력받아 1~9까지 출력해 보세요.
    # 연습 3: 1~100 중 짝수만 출력해 보세요.
    # 연습 4: 숫자 맞히기 게임에 시도 횟수 제한을 추가해 보세요.
    print("연습 문제는 함수 주석의 안내를 보고 직접 작성해 보세요.")


def main():
    # 다시 해보고 싶은 실습의 주석을 풀어 실행하세요.
    practice_variables_and_math()
    practice_printing()
    practice_nested_loops()
    # number_guessing_game()  # 입력을 받는 게임을 실행하려면 주석 해제
    practice_exercises()


if __name__ == "__main__":
    main()
