"""random, input, 조건문, 반복문을 활용한 숫자 맞히기 게임."""

import random


def number_guessing_game():
    """1부터 100 사이의 숫자를 맞히는 게임을 실행합니다."""
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
