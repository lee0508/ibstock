from fastapi import APIRouter

from app.schemas.stock import SearchRequest
from app.services.db import db_service
from app.services.faiss_store import faiss_store
from app.services.stock_answer import generate_stock_answer


router = APIRouter(prefix="/stock")


def _query_tokens(query: str) -> list[str]:
    normalized = query.replace("/", " ").replace(",", " ").strip().lower()
    tokens = [token for token in normalized.split() if token]
    if normalized and normalized not in tokens:
        tokens.append(normalized)
    unique = []
    for token in tokens:
        if token not in unique:
            unique.append(token)
    return unique


def _contains_token(text: str, token: str) -> bool:
    return token in (text or "").lower()


def _rerank_score(item: dict, tokens: list[str]) -> float:
    if not tokens:
        return float(item.get("score") or 0.0)

    title = (item.get("title") or "").lower()
    description = (item.get("description") or item.get("raw_text") or "").lower()
    stocks = [value.lower() for value in (item.get("stocks") or [])]
    ib_names = [value.lower() for value in (item.get("ib_names") or [])]
    sectors = [value.lower() for value in (item.get("sectors") or ([] if not item.get("sector") else [item.get("sector")]))]

    stock_joined = " ".join(stocks)
    ib_joined = " ".join(ib_names)
    sector_joined = " ".join(sectors)

    lexical = 0.0
    for token in tokens:
        if _contains_token(stock_joined, token):
            lexical += 4.0
        if _contains_token(ib_joined, token):
            lexical += 3.0
        if _contains_token(title, token):
            lexical += 2.0
        if _contains_token(sector_joined, token):
            lexical += 2.0
        if _contains_token(description, token):
            lexical += 1.0

    vector_score = float(item.get("score") or 0.0)
    return lexical + (vector_score * 0.1)


def format_search_item(item: dict) -> dict:
    snippet_source = item.get("description") or item.get("searchable_text") or ""
    snippet = snippet_source.replace("\n", " ").strip()[:240]
    return {
        "video_id": item.get("video_id"),
        "title": item.get("title"),
        "published_at": item.get("published_at"),
        "views": item.get("views"),
        "category": item.get("category"),
        "stocks": item.get("stocks") or [],
        "ib_names": item.get("ib_names") or [],
        "sectors": item.get("sectors") or ([] if not item.get("sector") else [item.get("sector")]),
        "source_url": item.get("source_url"),
        "score": item.get("score"),
        "snippet": snippet,
    }


async def resolve_search_items(query: str, limit: int) -> list[dict]:
    exact_items = db_service.search_video_matches(query, limit=limit)
    faiss_items = await faiss_store.search(query, limit=limit * 2)
    tokens = _query_tokens(query)

    merged = []
    seen = set()

    for item in exact_items + faiss_items:
        video_id = item.get("video_id")
        dedup_key = video_id or f"{item.get('title')}|{item.get('published_at')}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        item["score"] = _rerank_score(item, tokens)
        merged.append(item)

    if merged:
        merged.sort(key=lambda row: row.get("score") or 0.0, reverse=True)
        return merged[:limit]

    fallback = db_service.search_stock_mentions(query, limit=limit)
    for row in fallback:
        row["score"] = _rerank_score(row, tokens)
    fallback.sort(key=lambda row: row.get("score") or 0.0, reverse=True)
    return fallback[:limit]


@router.get("/sectors")
async def list_sectors():
    return {"items": db_service.list_sectors()}


@router.get("/ib-supply")
async def list_ib_supply(limit: int = 20):
    return {"items": db_service.list_ib_supply(limit=limit)}


@router.get("/index-info")
async def index_info():
    return faiss_store.info()


@router.post("/search")
async def search_stock(payload: SearchRequest):
    items = await resolve_search_items(payload.query, payload.limit)
    return {
        "query": payload.query,
        "mode": payload.mode,
        "items": [format_search_item(item) for item in items],
    }


@router.post("/query")
async def query_stock(payload: SearchRequest):
    items = await resolve_search_items(payload.query, payload.limit)
    answer = await generate_stock_answer(payload.query, items)
    return {
        "query": payload.query,
        "answer": answer,
        "items": [format_search_item(item) for item in items],
    }
