from decimal import Decimal, ROUND_DOWN


def calc_order(u_type, price, qty, coupon):
    """회원 할인과 쿠폰을 적용한 주문 금액을 원 단위 정수로 반환합니다."""
    # 예상하지 못한 회원 등급은 할인 누락으로 이어지지 않도록 명시적으로 거부합니다.
    if u_type not in (1, 2, 3):
        raise ValueError("u_type은 1, 2, 3 중 하나여야 합니다.")

    # bool은 int의 하위 타입이므로 type(...) is int로 정수 입력만 허용합니다.
    if type(price) is not int or price < 0:
        raise ValueError("price는 0 이상의 정수여야 합니다.")
    if type(qty) is not int or qty < 0:
        raise ValueError("qty는 0 이상의 정수여야 합니다.")

    # 대소문자와 앞뒤 공백 차이를 정리해 'yes', ' YES '도 쿠폰으로 인식합니다.
    coupon_code = coupon.strip().upper() if isinstance(coupon, str) else None
    if coupon_code not in ("YES", "NO"):
        raise ValueError('coupon은 "YES" 또는 "NO"여야 합니다.')

    # Decimal을 사용해 할인율 계산에서 부동소수점 오차를 피합니다.
    discount_rates = {1: Decimal("0.95"), 2: Decimal("0.90"), 3: Decimal("0.80")}
    total = Decimal(price * qty) * discount_rates[u_type]

    if coupon_code == "YES":
        total -= Decimal(3000)

    # 쿠폰이 주문 금액보다 커도 결제 금액은 0원 아래로 내려가지 않습니다.
    total = max(total, Decimal(0))

    # 기존 함수처럼 소수 원 단위는 버림 처리하며, 정책을 코드에 명확히 남깁니다.
    return int(total.to_integral_value(rounding=ROUND_DOWN))


# 기존 예시 입력의 'yes'도 쿠폰으로 처리되는지 확인하는 실행 예시입니다.
result = calc_order(1, 100, 20, "yes")
print(result)  # 1900원 - 3000원 쿠폰 = 0원
