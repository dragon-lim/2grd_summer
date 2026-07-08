import asyncio
import time
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()   # .env의 API 키를 환경변수로 로드 (인증에 필요)

MODEL = "claude-haiku-4-5"


# ─────────────────────────────────────────────
# LLM에 질문 하나를 보내고 답변(completion)을 받아오는 함수
# ─────────────────────────────────────────────
async def ask(client: AsyncAnthropic, question: str) -> str:
    response = await client.messages.create(
        model=MODEL,
        max_tokens=1000,
        # max_tokens은 context window가 지정되어 있어도 토큰을 아끼려고 제한한다
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text


# ═════════════════════════════════════════════
# [실습 1] 순차 실행 - await를 코루틴에 바로 붙임
#   → task 1개씩 처리, 겹치지 않아 6초 걸림 하지만 의미 없는 비동기이다.
#   → 제어권을 event loop에 넘겨도 q는 다른 작업이 없어 곧바로 돌아와서 종료됨
# ═════════════════════════════════════════════
# async def make_order(item, taken_time):
#     print(f"{item} 접수")
#     await asyncio.sleep(taken_time)   # 양보하지만, 받을 다른 코루틴이 없음
#     print(f"{item} done.")
#
# async def main():
#     start_time = time.time()
#     result1 = await make_order("라떼", 3)   # 라떼 끝날 때까지 대기 → 다음으로
#     result2 = await make_order("아아", 2)
#     result3 = await make_order("우유", 1)
#     elapsed_time = time.time() - start_time
#     print(f"{result1} \n {result2} \n {result3}")
#     print(f"총 소요시간 : {elapsed_time}")   # 3+2+1 = 6초


# ═════════════════════════════════════════════
# [실습 2] create_task로 여러 개 먼저 시작 → 나중에 await
#   → task 3가지를 미리 큐에 넣어 대기가 겹쳐짐, 3초 걸림
#   ※ 아래 'await result1, result2, result3' 는 사실 result1만 await되는 버그!
#     제대로 하려면 각각 await 하거나 gather로 묶어야 함(다음시간)
# ═════════════════════════════════════════════
# async def main():
#     start_time = time.time()
#     task1 = asyncio.create_task(make_order("라떼", 3))  
#     task2 = asyncio.create_task(make_order("아아", 2))
#     task3 = asyncio.create_task(make_order("우유", 1))
#     await task1 task2 task3
#     # 시작하는 task만 await 효과먹음
#     elapsed_time = time.time() - start_time
#     print(f"총 소요시간 : {elapsed_time}")   # 약 3초 (가장 긴 라떼 기준)


# ═════════════════════════════════════════════
# [실습 3] LLM에 여러 질문을 동시에 보내기 (실전!)
#   → LLM API 호출 = In/Out 바운드(응답 대기) → 비동기로 겹치면 빨라짐
#   → 이것이 "AI agent에서 비동기를 처리하는 방법"
# ═════════════════════════════════════════════
async def main():
    start_time = time.time()
    client = AsyncAnthropic()

    # 보낼 질문 목록
    questions = ["파이썬이 뭐야?", "파이썬이 가장 쉬운 이유는?", "go 언어와 파이썬의 차이는?"]

    # 컴프리헨션으로 코루틴 리스트를 만들고, *로 언패킹해 gather에 전달
    # gather = 질문(3가지)를 동시에 보내고, 모든 답변(3가지) 다 올 때까지 기다림
    results = await asyncio.gather(
        *[ask(client, q) for q in questions]
    )

    # ── 참고: create_task로도 같은 일을 할 수 있음 (하드코딩 버전) ──
    # task1 = asyncio.create_task(ask(client, "파이썬이 뭐야?"))
    # task2 = asyncio.create_task(ask(client, "자바가 뭐야?"))
    # task3 = asyncio.create_task(ask(client, "go는 뭐야?"))
    # result1 = await task1
    # result2 = await task2
    # result3 = await task3

    elapsed_time = time.time() - start_time
    for answer in results:
        print(answer)
        print("*" * 50)
    print(f"총 소요시간 : {elapsed_time}")


if __name__ == "__main__":
    asyncio.run(main())


# ─────────────────────────────────────────────
# TODO (다음에 할 것)
#  - 예외 처리: 일부 질문이 실패해도 나머지는 살리기!
#  - 질문이 100개면? → LLM 서버는 동시 처리 범위(동시 접속자 수)가 제한됨
#    → 한 번에 몇 개씩만 나눠 보내는 '동시 실행 개수 제한'이 필요
# ─────────────────────────────────────────────
