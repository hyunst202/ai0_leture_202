from pydantic import BaseModel, Field


class Product(BaseModel):
   title: str = field(min_length=2, max_length=60)
   TODO Price: 0 보다 커야 함
   TODO stock: 0 이상, 기본값 0
   TODO sku: SKU-와 숫자 네 자리 패턴
   __pydantic_fields_set__


def main() -> None
    print('TODO: 정상 상품 및 잘못된 상품을 테스트하세요.')


if __name__ == '__main__':
    main()
    