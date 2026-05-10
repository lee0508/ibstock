import httpx

from app.core.config import settings


def build_fallback_answer(query: str, items: list[dict]) -> str:
    if not items:
        return f"'{query}'와 직접 연결되는 영상 근거를 찾지 못했습니다."
    top = items[0]
    title = top.get("title") or "제목 없음"
    stocks = ", ".join(top.get("stocks") or []) or "종목 미추출"
    ib_names = ", ".join(top.get("ib_names") or []) or "기관 미추출"
    return f"가장 가까운 근거 영상은 '{title}'입니다. 관련 종목은 {stocks}, 관련 기관은 {ib_names}로 정리됩니다."


async def generate_stock_answer(query: str, items: list[dict]) -> str:
    if not items:
        return f"'{query}'와 직접 연결되는 검색 결과가 없어 요약을 생성하지 않았습니다."

    context_lines = []
    for idx, item in enumerate(items[:4], start=1):
        context_lines.append(
            "\n".join(
                [
                    f"[{idx}] 제목: {item.get('title') or ''}",
                    f"[{idx}] 날짜: {item.get('published_at') or ''}",
                    f"[{idx}] 종목: {', '.join(item.get('stocks') or [])}",
                    f"[{idx}] 기관: {', '.join(item.get('ib_names') or [])}",
                    f"[{idx}] 섹터: {', '.join(item.get('sectors') or [])}",
                    f"[{idx}] 요약텍스트: {(item.get('description') or item.get('searchable_text') or '')[:700]}",
                ]
            )
        )

    prompt = "\n\n".join(
        [
            "당신은 한국 주식 정보 검색 도우미다.",
            "주어진 근거만 사용해서 4문장 이내로 간결하게 답하라.",
            "확실하지 않으면 추정이라고 밝히고, 투자 권유 문구는 쓰지 마라.",
            f"질문: {query}",
            "근거:",
            "\n\n".join(context_lines),
        ]
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "num_predict": 300,
                    },
                },
            )
            response.raise_for_status()
            answer = response.json().get("response", "").strip()
            if answer:
                return answer
    except Exception:
        pass

    return build_fallback_answer(query, items)
