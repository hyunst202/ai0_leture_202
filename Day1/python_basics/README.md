# Python 기초 실습 모듈

## 브라우저에서 보기

`index.html` 파일을 파일 탐색기에서 더블 클릭하면 브라우저에서 예제 결과를 볼 수 있습니다. 별도의 서버나 패키지 설치는 필요하지 않습니다. 숫자 맞히기 게임은 페이지에서 바로 실행됩니다.

## 파이썬 코드 실행

프로젝트 루트(`python_basics` 폴더의 상위 폴더)에서 다음 명령을 실행하세요.

```powershell
python -m python_basics
```

기본 실행에서는 변수와 사칙연산, 구구단, 연습 문제 안내가 출력됩니다. 숫자 맞히기 게임을 실행하려면 `__main__.py`에서 `number_guessing_game()` 줄의 주석을 해제한 뒤 다시 실행하세요.

## 파일 구성

- `index.html`: 브라우저에서 보는 실습 결과와 숫자 맞히기 게임
- `arithmetic.py`: 변수와 사칙연산
- `multiplication.py`: print 및 반복문 구구단
- `guessing_game.py`: 파이썬 숫자 맞히기 게임
- `exercises.py`: 직접 풀어볼 연습 문제
- `__main__.py`: `python -m python_basics` 실행 진입점
- `__init__.py`: 패키지 초기화
