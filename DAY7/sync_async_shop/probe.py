"""실행 중인 앱에 실제 HTTP 요청을 보내 네 가지 방식의 차이를 측정합니다."""

import argparse
import asyncio
from time import perf_counter

import httpx


MODES = ("blocking", "async-sequential", "async-concurrent", "threaded")


async def compare(client: httpx.AsyncClient, mode: str, visitors: int, scale: float):
    started = perf_counter()

    async def one(visitor):
        response = await client.get(
            "/api/product", params={"mode": mode, "visitor": visitor, "scale": scale}
        )
        response.raise_for_status()
        return response.json()

    requests = [asyncio.create_task(one(i + 1)) for i in range(visitors)]
    # 상품 조회가 실행 중일 때 별도 요청을 보냅니다.
    await asyncio.sleep(0.1)
    health_started = perf_counter()
    health = await client.get("/health")
    health.raise_for_status()
    health_ms = (perf_counter() - health_started) * 1000
    responses = await asyncio.gather(*requests)
    elapsed = perf_counter() - started
    print(f"{mode:20} | total {elapsed:5.2f}s | /health {health_ms:7.1f}ms")
    return {"mode": mode, "elapsed": elapsed, "health_ms": health_ms, "responses": responses}


def verify_measurements(results, visitors):
    by_mode = {result["mode"]: result for result in results}
    for mode, result in by_mode.items():
        assert len(result["responses"]) == visitors, mode
        for response in result["responses"]:
            assert response["mode"] == mode
            spans = response["services"]
            assert {span["key"] for span in spans} == {"stock", "reviews", "delivery"}
            assert all(0 <= span["start_ms"] < span["end_ms"] <= response["elapsed_ms"] + 1 for span in spans)
            if mode in ("blocking", "async-sequential"):
                assert all(spans[i]["end_ms"] <= spans[i + 1]["start_ms"] for i in range(2)), mode
            else:
                # 세 조회가 실제로 겹쳤는지 서버 측정값으로 확인합니다.
                assert max(s["start_ms"] for s in spans) < min(s["end_ms"] for s in spans), mode

    blocking = by_mode["blocking"]
    # 순서가 바뀌어 도착하더라도 blocking 방문자의 서버 실행 구간은 겹치지 않아야 합니다.
    spans = sorted(blocking["responses"], key=lambda r: r["server_started_ms"])
    for previous, following in zip(spans, spans[1:]):
        assert previous["server_started_ms"] + previous["elapsed_ms"] <= following["server_started_ms"] + 2
    for mode in MODES[1:]:
        assert blocking["health_ms"] > by_mode[mode]["health_ms"] + 200, "Use exactly one Uvicorn worker."
    assert by_mode["async-sequential"]["elapsed"] > by_mode["async-concurrent"]["elapsed"] * 1.4
    if visitors > 1:
        assert blocking["elapsed"] > by_mode["async-sequential"]["elapsed"] * 1.5


async def main(args):
    async with httpx.AsyncClient(base_url=args.url, timeout=60, trust_env=False) as client:
        if args.verify:
            for path in ("/", "/static/styles.css", "/static/app.js", "/docs", "/openapi.json", "/api/config"):
                response = await client.get(path)
                response.raise_for_status()
            for params in ({"mode": "unknown"}, {"scale": 0}, {"scale": "nan"}, {"visitor": 4}):
                response = await client.get("/api/product", params=params)
                assert response.status_code == 422, params
        print(f"visitors={args.visitors}, delay scale={args.scale}, server={args.url}\n")
        results = []
        for mode in MODES:
            results.append(await compare(client, mode, args.visitors, args.scale))
        if args.verify:
            verify_measurements(results, args.visitors)
            print("\nPASS: HTTP routes, input validation, service overlap, visitor scheduling, /health responsiveness")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8017")
    parser.add_argument("--visitors", type=int, choices=(1, 3), default=3)
    parser.add_argument("--scale", type=float, choices=(0.25, 0.5, 1.0, 1.5), default=1.0)
    parser.add_argument("--verify", action="store_true", help="측정 결과와 입력 검증까지 검사")
    arguments = parser.parse_args()
    try:
        asyncio.run(main(arguments))
    except (httpx.HTTPError, AssertionError) as error:
        parser.exit(1, f"ERROR: {error}\n서버 주소와 --workers 1 설정을 확인해 주세요.\n")
