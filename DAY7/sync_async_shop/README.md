# Slowroom — 동기와 비동기 실험실

쇼핑몰 **상품 상세 페이지에서 재고·리뷰·배송 정보를 가져오는 상황**으로 DAY7의 동기·비동기 처리를 재현합니다. 화면에서 처리 방식, 동시 방문자 수, 지연 배율을 바꾸고 실제 HTTP 응답 시간을 비교합니다.

FastAPI + Python 표준 `asyncio` + HTML/CSS/JavaScript로 작성했습니다. 터미널 비교에는 HTTPX를 사용합니다. 프런트엔드 빌드, Node.js, DB, API 키는 필요하지 않습니다. 상품 데이터는 고정된 예제이며, 외부 서비스의 I/O 대기를 `sleep`으로 모의합니다.

## 1. 실행 방법 (Windows PowerShell)

### 현재 작업 공간에서 바로 실행

이 작업 공간에는 실제 동작 검증을 위해 앱 폴더 안에 별도의 Python과 의존성을 준비했습니다. 기존 루트 `.venv`를 사용하지 않고 다음 명령으로 바로 실행할 수 있습니다.

```powershell
cd C:\AI4\DAY7\sync_async_shop
.\.runtime\python\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8017 --workers 1
```

검증용 `.runtime/`은 Git에서 제외됩니다. 다른 PC나 새 체크아웃에서는 아래 일반 설치 방법을 사용하세요.

### 일반 설치 및 실행

Python 3.10 이상을 설치한 환경에서 실행하세요. 이 앱 전용 가상환경을 만들어 기존 DAY7 환경과 분리합니다.

```powershell
cd C:\AI4\DAY7\sync_async_shop
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8017 --workers 1
```

- 앱 화면: <http://127.0.0.1:8017>
- Swagger API 문서: <http://127.0.0.1:8017/docs>
- 서버 종료: 터미널에서 `Ctrl+C`

`py` 명령이 없다면 `python --version`을 확인하고 두 번째 명령을 `python -m venv .venv`로 바꾸세요. 두 명령 모두 없다면 [Python 공식 배포판](https://www.python.org/downloads/windows/)을 설치하고 터미널을 다시 여세요.

가상환경 활성화는 필요하지 않습니다. 위처럼 Python 실행 파일을 직접 호출하면 PowerShell 스크립트 실행 정책을 변경하지 않아도 됩니다. 기존 저장소 루트 `.venv`에서 원본 Python 경로를 찾지 못한다는 오류가 나도, 새 하위 폴더에서 생성한 `.venv`를 사용하면 됩니다. 새 환경 생성 자체가 실패하면 Python 설치 상태부터 확인하세요.

**워커 1개로 실행해야 의도한 차이가 잘 보입니다.** 워커가 여러 개이면 다른 프로세스가 `/health` 요청을 처리해 동기 블로킹 효과가 가려지고, 프로세스별 타임라인을 한 실험처럼 비교하기 어려워집니다. 예제의 타이밍은 한 탭에서 한 실험씩 실행하는 상황을 기준으로 합니다.

## 2. 화면에서 실험하기

1. 기본 상태의 **비동기 · 함께 기다리기**로 `상품 정보 불러오기`를 누릅니다. 약 1.8초 뒤 상품 정보가 완성됩니다.
2. **동기 호출 · 서버 멈춤**으로 바꿔 실행합니다. 약 4초가 걸리고, 별도로 보낸 `/health` 응답도 늦어집니다.
3. 방문자를 **3명**으로 바꾸어 두 방식을 다시 비교합니다. 동기 블로킹은 약 12초, 비동기 동시 처리는 약 1.8초가 걸립니다.
4. **비동기 · 하나씩 기다리기**도 실행해 보세요. 약 4초가 걸리지만 다른 방문자의 요청과 `/health`는 계속 처리됩니다.
5. **동기 함수 · 스레드로 분리**에서는 같은 `time.sleep()` 함수를 `asyncio.to_thread()`로 옮겨 실행합니다. 이벤트 루프의 응답성을 회복합니다.

`네 가지 방식 순서대로 비교`는 같은 설정으로 네 실험을 차례로 실행합니다. 빠르게 확인하려면 지연을 **0.25배**로 바꾸세요. 기록은 현재 탭의 메모리에 최근 12회까지 남고 새로고침하면 초기화됩니다. `기록 지우기`로 비울 수 있습니다.

## 3. 무엇이 달라지나요?

기본 대기 시간은 재고 1.2초, 리뷰 1.8초, 배송 1.0초입니다. 모든 방식에서 같은 데이터와 같은 지연을 사용합니다.

| 처리 방식 | 핵심 코드 | 방문자 1명 | 방문자 3명 전체 | 상품 조회 중 다른 요청 |
| --- | --- | ---: | ---: | --- |
| 동기 호출 · 서버 멈춤 | `async def` 안에서 `time.sleep()` 직접 실행 | 약 4초 | 약 12초 | 이벤트 루프가 막혀 기다림 |
| 비동기 · 하나씩 기다리기 | 조회마다 `await asyncio.sleep()` | 약 4초 | 약 4초 | 대기 중 처리 가능 |
| 비동기 · 함께 기다리기 | `await asyncio.gather(...)` | 약 1.8초 | 약 1.8초 | 대기 중 처리 가능 |
| 동기 함수 · 스레드로 분리 | `gather(to_thread(...), ...)` | 약 1.8초 | 약 1.8초 | 이벤트 루프에서 처리 가능 |

네트워크·OS 스케줄링 등에 따라 실측값은 달라집니다. 스레드 방식도 요청이 많아지면 스레드 수에 따른 대기가 생길 수 있습니다.

### 화면의 측정값

- **전체 조회 시간:** 브라우저가 방문자 요청을 보내기 시작한 때부터 모든 상품 응답을 받은 때까지 측정합니다.
- **다른 요청의 최대 대기:** 상품 조회 시작 약 120ms 뒤부터 `/health`에 실제 요청을 보냅니다. 응답 후 약 300ms 간격으로 반복하며, 한 번에 하나만 보냅니다. HTTP 왕복 시간을 표시하며 서버 대기와 네트워크 시간이 함께 포함됩니다. 응답을 기다리는 동안에는 현재 대기를 `≥`로 표시합니다.
- **타임라인:** 응답에 포함된 서버의 실제 시작·종료 시각으로 그립니다. 방문자 간 시작 위치도 같은 서버의 단조 시계로 맞춥니다. 브라우저에서 요청이 전송되기 전의 대기나 네트워크 시간은 포함하지 않습니다. 응답 전에는 실행 구간을 알 수 없어 완료 후에 표시합니다.
- **상품 정보 카드:** 첫 번째 방문자의 조회 결과를 보여줍니다. 같은 상품을 조회하므로 다른 방문자도 같은 결과를 받습니다.

`async`라는 이름만 붙여도 동시 실행되는 것은 아닙니다. 순차 `await`와 `gather`를 비교하면 **서버가 다른 일을 할 수 있는가**와 **한 페이지의 대기를 겹치는가**가 서로 다른 질문임을 볼 수 있습니다.

FastAPI는 일반 `def` 경로 함수를 스레드 풀에서 실행합니다. 따라서 모든 동기 경로가 서버를 멈추는 것은 아닙니다. 이 예제의 첫 번째 방식은 **`async def` 안에서 블로킹 일반 함수를 직접 호출하는 실수**를 의도적으로 재현합니다. 실제 비동기 HTTP 요청에서는 `await httpx.AsyncClient().get(...)` 같은 비동기 I/O를 사용합니다. `asyncio`가 CPU 계산 자체를 빠르게 만드는 것은 아닙니다.

## 4. 터미널에서도 비교하기

서버를 켜 둔 채 새 터미널에서 실행합니다. DAY7/probe.py와 같은 `httpx.AsyncClient`, `asyncio.gather()`, `perf_counter()`를 활용합니다.

```powershell
cd C:\AI4\DAY7\sync_async_shop
.\.venv\Scripts\python.exe probe.py
```

빠른 검증 명령:

```powershell
.\.venv\Scripts\python.exe probe.py --scale 0.25 --visitors 3 --verify
```

현재 작업 공간의 검증용 Python으로 실행할 때는 다음 명령을 사용합니다.

```powershell
.\.runtime\python\python.exe probe.py --scale 0.25 --visitors 3 --verify
```

각 방식의 전체 시간과 별도 `/health` 요청의 응답 시간이 출력됩니다. `--verify`는 정적 파일·문서·API 연결, 잘못된 입력의 422 응답, 실제 조회 구간의 겹침, 동기 블로킹 시 방문자 실행 순서와 health 지연을 검사합니다. 서버 포트가 다르면 `--url http://127.0.0.1:다른포트`를 추가하세요.

API 직접 호출 예시:

```powershell
Invoke-RestMethod "http://127.0.0.1:8017/api/product?mode=async-concurrent&visitor=1&scale=1"
```

`mode` 허용값은 `blocking`, `async-sequential`, `async-concurrent`, `threaded`입니다. `visitor`는 1~3, `scale`은 0.25~2.0 범위입니다. `visitor`는 방문자 식별 번호이며, 동시 방문자 수만큼 클라이언트에서 HTTP 요청을 함께 보내는 구조입니다.

## 5. 파일 구성과 기존 DAY7 코드 연결

```text
sync_async_shop/
├── app.py              # FastAPI, 모의 서비스, 네 가지 조회 방식
├── probe.py            # HTTPX 동시 요청 비교 및 통합 검증
├── requirements.txt
├── README.md
└── static/
    ├── index.html      # 상품 페이지 + 실험 화면
    ├── styles.css      # PC/모바일 레이아웃
    └── app.js          # 실제 요청, health 측정, 타임라인, 기록
```

| 기존 코드 | 이 앱에서 확장한 부분 |
| --- | --- |
| `DAY7/main2.py`의 `legacy_lookup()` 직접 호출 | `blocking` 모드 |
| `DAY7/main.py`의 `asyncio.to_thread()` | `threaded` 모드 |
| `DAY7/demo.py`, `demo2.py`의 순차 `await` / `gather` | `async-sequential` / `async-concurrent` 모드 |
| `DAY7/probe.py`의 HTTPX 동시 요청과 시간 측정 | 화면의 동시 방문자, 새 `probe.py` |

기존 DAY7 파일은 수정하지 않습니다.

공식 설명: [FastAPI의 async와 동시성](https://fastapi.tiangolo.com/async/), [Python asyncio의 gather / to_thread](https://docs.python.org/3/library/asyncio-task.html).
