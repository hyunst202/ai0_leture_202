# What          : 무엇을 만들지
# Consistants   : 어떤 제약으로 동작해야 하는지
# How           : 구현은 어떻게
# Vive check    : 결과를 검증
# 3대 핵심 룰 P(prompt) -> G(Generatior) -> V(Valitor)
# P(Prompt) : 입력(input) , 출력(output) , 알고리즘 제약 조건 , 함수 명시
# Validator : 결과검증, 테스트케이스 검증

# 1부터 N까지의 짝수 합과 개수 구하기
# Bed : 짝수 합 구해줘

'''
[Problem] 1부터 n까지의 정수 중 짝수들의 합과 짝수의 총 개수를 계산한다
[Funtion] calculate_even_sum_and_count()
[Rules]
    - n이 미만인 경우 합 0, 개수 0을 반환할 것
    - for 문과 if 문을 활용하여 짝수( i % 2 ==)를 판단할 것
[Output]    {"sum": int, "count":int }
'''

# 실습규칙
'''
문제정의 / 입력값 / 출력값 / 제약조건을 작성
assert 함수를 활용하여 테스트 케이스
'''