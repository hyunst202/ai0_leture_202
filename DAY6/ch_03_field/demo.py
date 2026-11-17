# field 범위, 길이 패턴에 대해서 엄격하게 검사
from pydantic import BaseModel, Field, ValidationError, Emailstr, ConfigDict
from typing import literal

class Registeration(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    name : str = Field(..., min_length=2, max_length=20,description='실명')
    age : int = Field(..., ge=14, le=100)
    email : Emailstr
    level : lieral['basic','premium','vip'] = 'basic'
    code : str = Field(pattern=r'^STU-[0-9]{4}$')  # STU-0001
    agreed : bool=Field(strict=True)

def main() -> None:
    registration(name='lee', age = '50', email='lee@abc.com',code='STU-0001')
    print('검증성공', user1.model_dump())
    print('오류확인')
    try:
        user2 = Registeration(name='lee', age = '500', email='lee@abc.com',code='STU-001')
    except ValidationError as e:
        print(e.errors()[0]['loc'],e.errors()[0]['type'])

if __name__ == '__main__':
    main()

