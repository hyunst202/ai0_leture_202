"""기초 실습 패키지의 실행 진입점."""

from .arithmetic import practice_variables_and_math
from .exercises import practice_exercises
from .guessing_game import number_guessing_game
from .multiplication import practice_nested_loops, practice_printing


def main():
    """기본 실습을 실행합니다. 원하는 함수 호출을 조정해 사용하세요."""
    practice_variables_and_math()
    practice_printing()
    practice_nested_loops()
    # number_guessing_game()  # 게임을 실행하려면 주석을 해제하세요.
    practice_exercises()


if __name__ == "__main__":
    main()
