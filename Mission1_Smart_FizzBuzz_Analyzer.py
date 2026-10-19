"""Mission 1: Smart FizzBuzz Analyzer

[문제 정의]
1부터 limit까지의 각 정수를 FizzBuzz, Fizz, Buzz, Number로 분류하고
각 분류에 해당하는 숫자의 개수를 계산한다.

[입력값]
- limit (int): 순회할 마지막 정수

[출력값]
- dict: {"FizzBuzz": int, "Fizz": int, "Buzz": int, "Number": int}

[제약조건]
- 1부터 limit까지 순회한다.
- 3과 5의 공배수는 FizzBuzz로 센다.
- 3의 배수는 Fizz로, 5의 배수는 Buzz로 센다.
- 그 외 숫자는 Number로 센다.
- limit가 1 미만이면 모든 카운트를 0으로 반환한다.
"""


def analyze_fizzbuzz(limit: int) -> dict:
    """Count the FizzBuzz categories for the integers from 1 through limit."""
    counts = {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 0}

    for number in range(1, limit + 1):
        if number % 3 == 0 and number % 5 == 0:
            counts["FizzBuzz"] += 1
        elif number % 3 == 0:
            counts["Fizz"] += 1
        elif number % 5 == 0:
            counts["Buzz"] += 1
        else:
            counts["Number"] += 1

    return counts


def run_assertions() -> None:
    """Run representative examples, boundary checks, and range invariants."""
    zero_counts = {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 0}

    # Empty and negative ranges must return every key with a zero count.
    for limit in (-100, -3, -1, 0):
        result = analyze_fizzbuzz(limit)
        assert result == zero_counts
        assert tuple(result) == ("FizzBuzz", "Fizz", "Buzz", "Number")

    # Explicit expected results cover values before, at, and after multiples.
    expected_cases = {
        1: {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 1},
        2: {"FizzBuzz": 0, "Fizz": 0, "Buzz": 0, "Number": 2},
        3: {"FizzBuzz": 0, "Fizz": 1, "Buzz": 0, "Number": 2},
        5: {"FizzBuzz": 0, "Fizz": 1, "Buzz": 1, "Number": 3},
        6: {"FizzBuzz": 0, "Fizz": 2, "Buzz": 1, "Number": 3},
        10: {"FizzBuzz": 0, "Fizz": 3, "Buzz": 2, "Number": 5},
        14: {"FizzBuzz": 0, "Fizz": 4, "Buzz": 2, "Number": 8},
        15: {"FizzBuzz": 1, "Fizz": 4, "Buzz": 2, "Number": 8},
        16: {"FizzBuzz": 1, "Fizz": 4, "Buzz": 2, "Number": 9},
        30: {"FizzBuzz": 2, "Fizz": 8, "Buzz": 4, "Number": 16},
    }
    for limit, expected in expected_cases.items():
        result = analyze_fizzbuzz(limit)
        assert result == expected
        assert all(type(count) is int and count >= 0 for count in result.values())
        assert sum(result.values()) == limit

    # Exhaustive small-range checks: categories are exclusive and cumulative.
    previous = zero_counts.copy()
    for limit in range(1, 101):
        result = analyze_fizzbuzz(limit)
        assert sum(result.values()) == limit
        assert result["FizzBuzz"] == limit // 15
        assert result["Fizz"] == limit // 3 - limit // 15
        assert result["Buzz"] == limit // 5 - limit // 15
        assert result["Number"] == limit - limit // 3 - limit // 5 + limit // 15
        assert all(result[key] >= previous[key] for key in result)
        previous = result


if __name__ == "__main__":
    run_assertions()
    print("모든 assert 검증을 통과했습니다.")
    print(analyze_fizzbuzz(15))
