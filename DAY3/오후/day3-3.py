from decimal import Decimal, ROUND_DOWN


class Order:
    """주문 정보를 보관하고 할인 규칙에 따라 결제 금액을 계산합니다."""

    # 회원 유형별 할인율을 클래스에 모아두어 규칙을 한곳에서 관리합니다.
    DISCOUNT_RATES = {
        1: Decimal("0.95"),  # 1등급: 5% 할인
        2: Decimal("0.90"),  # 2등급: 10% 할인
        3: Decimal("0.80"),  # 3등급: 20% 할인
    }
    COUPON_DISCOUNT = Decimal("3000")

    def __init__(self, user_type, price, quantity, coupon):
        # 함수의 매개변수들을 주문 객체의 속성으로 보관합니다.
        self.user_type = user_type
        self.price = price
        self.quantity = quantity
        self.coupon = coupon

    def calculate_total(self):
        """회원 할인과 쿠폰을 적용한 최종 금액을 원 단위 정수로 반환합니다."""
        # 함수에 흩어져 있던 입력 검증을 주문 객체의 계산 과정에 둡니다.
        if self.user_type not in self.DISCOUNT_RATES:
            raise ValueError("user_type은 1, 2, 3 중 하나여야 합니다.")
        if type(self.price) is not int or self.price < 0:
            raise ValueError("price는 0 이상의 정수여야 합니다.")
        if type(self.quantity) is not int or self.quantity < 0:
            raise ValueError("quantity는 0 이상의 정수여야 합니다.")

        # 'yes', ' YES '처럼 대소문자나 앞뒤 공백이 다른 입력도 정규화합니다.
        coupon_code = self.coupon.strip().upper() if isinstance(self.coupon, str) else None
        if coupon_code not in ("YES", "NO"):
            raise ValueError('coupon은 "YES" 또는 "NO"여야 합니다.')

        # 기존 함수와 동일하게 상품 금액에 회원 할인을 먼저 적용합니다.
        total = Decimal(self.price * self.quantity) * self.DISCOUNT_RATES[self.user_type]

        # 쿠폰 사용 시 3,000원을 차감하고, 총액은 0원보다 작아지지 않게 합니다.
        if coupon_code == "YES":
            total -= self.COUPON_DISCOUNT
        total = max(total, Decimal("0"))

        # 기존 코드의 int 변환과 같이 소수점 아래 원 단위는 버립니다.
        return int(total.to_integral_value(rounding=ROUND_DOWN))


# 기존의 함수 호출을 객체 생성과 메서드 호출로 바꾼 사용 예시입니다.
order = Order(user_type=1, price=100, quantity=20, coupon="yes")
result = order.calculate_total()
print(result)  # 회원 할인 후 쿠폰을 적용하면 0원
