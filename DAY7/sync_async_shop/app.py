"""DAY7의 동기/비동기 코드를 상품 상세 페이지 조회로 확장한 실습 앱."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Literal

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


BASE_DIR = Path(__file__).resolve().parent
Mode = Literal["blocking", "async-sequential", "async-concurrent", "threaded"]

app = FastAPI(
    title="Slowroom · 동기와 비동기 실험실",
    description="재고·리뷰·배송 조회를 네 가지 방식으로 실행합니다. 지연은 로컬에서 모의합니다.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@dataclass(frozen=True)
class Service:
    key: str
    label: str
    seconds: float
    value: str
    detail: str


SERVICES = (
    Service("stock", "재고 조회", 1.2, "구매 가능", "현재 재고 24개 · 웜 화이트"),
    Service("reviews", "리뷰 조회", 1.8, "4.9 / 5.0", "128개의 리뷰 · 은은한 빛이 좋아요"),
    Service("delivery", "배송 조회", 1.0, "무료 배송", "주문 후 2~3일 내 도착 예상"),
)

MODES = [
    {
        "id": "blocking",
        "name": "동기 호출 · 서버 멈춤",
        "tag": "BLOCKING",
        "description": "async 함수 안에서 동기 함수를 직접 호출합니다. 기다리는 동안 다른 요청도 멈춥니다.",
        "code": "# async def product(...) 내부\nresults = [\n    legacy_lookup(s, scale, origin)\n    for s in SERVICES\n]  # 내부에서 time.sleep() 실행",
        "note": "의도적으로 이벤트 루프를 막는 코드입니다. 상품 조회 중 /health 응답도 늦어지는지 확인하세요.",
    },
    {
        "id": "async-sequential",
        "name": "비동기 · 하나씩 기다리기",
        "tag": "AWAIT",
        "description": "조회 하나를 기다린 뒤 다음 조회를 시작합니다. 대기 중에는 다른 요청을 처리합니다.",
        "code": "results = []\nfor s in SERVICES:\n    results.append(\n        await async_lookup(s, scale, origin)\n    )  # 내부에서 await asyncio.sleep()",
        "note": "await를 사용해도 순서대로 기다리면 한 방문자의 조회 시간은 합계입니다. 다른 방문자와 /health는 응답할 수 있습니다.",
    },
    {
        "id": "async-concurrent",
        "name": "비동기 · 함께 기다리기",
        "tag": "GATHER",
        "description": "독립적인 세 조회를 함께 시작합니다. 가장 느린 조회가 끝나면 페이지가 완성됩니다.",
        "code": "results = await asyncio.gather(\n    *(async_lookup(s, scale, origin)\n      for s in SERVICES)\n)",
        "note": "재고·리뷰·배송은 서로 독립적이므로 함께 기다릴 수 있습니다. I/O 대기를 겹쳐 전체 시간을 줄입니다.",
    },
    {
        "id": "threaded",
        "name": "동기 함수 · 스레드로 분리",
        "tag": "TO_THREAD",
        "description": "기존 동기 함수를 스레드에서 실행합니다. 이벤트 루프는 다른 요청을 계속 처리합니다.",
        "code": "results = await asyncio.gather(\n    *(asyncio.to_thread(\n        legacy_lookup, s, scale, origin\n    ) for s in SERVICES)\n)",
        "note": "동기 라이브러리를 바꾸기 어려울 때 활용합니다. 이 실험의 작은 요청 수에서는 비동기 동시 처리와 비슷한 시간이 나옵니다.",
    },
]


def result_for(service: Service, started: float, origin: float) -> dict:
    """실제로 실행된 구간을 기록합니다. 화면의 타임라인은 이 값을 사용합니다."""
    ended = time.perf_counter()
    return {
        "key": service.key,
        "label": service.label,
        "value": service.value,
        "detail": service.detail,
        "start_ms": round((started - origin) * 1000, 3),
        "end_ms": round((ended - origin) * 1000, 3),
    }


def legacy_lookup(service: Service, scale: float, origin: float) -> dict:
    """DAY7/main2.py의 동기 조회: 외부 API/DB 응답 대기를 흉내냅니다."""
    started = time.perf_counter()
    time.sleep(service.seconds * scale)
    return result_for(service, started, origin)


async def async_lookup(service: Service, scale: float, origin: float) -> dict:
    """실제 외부 호출 없이 비동기 I/O 대기를 재현합니다."""
    started = time.perf_counter()
    await asyncio.sleep(service.seconds * scale)
    return result_for(service, started, origin)


@app.get("/", include_in_schema=False)
async def index():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/config")
async def config():
    return {
        "modes": MODES,
        "services": [
            {"key": s.key, "label": s.label, "seconds": s.seconds} for s in SERVICES
        ],
    }


@app.get("/health")
async def health():
    """조회와 같은 이벤트 루프에서 실행되는 가벼운 요청."""
    return {"status": "ok"}


@app.get("/api/product")
async def product(
    mode: Mode = "async-concurrent",
    scale: float = Query(default=1.0, ge=0.25, le=2.0),
    visitor: int = Query(default=1, ge=1, le=3),
):
    origin = time.perf_counter()

    if mode == "blocking":
        # 의도된 안티패턴! async def 안의 일반 함수는 자동으로 스레드에 가지 않습니다.
        results = [legacy_lookup(service, scale, origin) for service in SERVICES]
    elif mode == "async-sequential":
        results = []
        for service in SERVICES:
            results.append(await async_lookup(service, scale, origin))
    elif mode == "async-concurrent":
        results = await asyncio.gather(
            *(async_lookup(service, scale, origin) for service in SERVICES)
        )
    else:  # threaded
        results = await asyncio.gather(
            *(asyncio.to_thread(legacy_lookup, service, scale, origin) for service in SERVICES)
        )

    return {
        "mode": mode,
        "visitor": visitor,
        "scale": scale,
        # 같은 서버 프로세스의 단조 시계. 방문자별 실행 위치를 맞추는 용도입니다.
        "server_started_ms": origin * 1000,
        "elapsed_ms": round((time.perf_counter() - origin) * 1000, 3),
        "services": results,
    }
