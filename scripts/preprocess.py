import json
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "shorts_latest.json"
OUT_PATH = PROJECT_ROOT / "data" / "processed" / "shorts_normalized.json"
SECTOR_PATH = PROJECT_ROOT / "data" / "reference" / "sector_keywords.json"
IB_PATH = PROJECT_ROOT / "data" / "reference" / "ib_aliases.json"
STOCKS_PATH = PROJECT_ROOT / "data" / "reference" / "stock_keywords.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_title(text: str) -> str:
    cleaned = re.split(r"\s*#", text, maxsplit=1)[0].strip()
    return cleaned or text.strip()


def clean_description(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    cut_markers = [
        "IB수급TV(IB FLOW TV)",
        "주식 코스피 코스닥",
        "구독과 좋아요 부탁드립니다",
    ]
    for marker in cut_markers:
        if marker in normalized:
            normalized = normalized.split(marker, 1)[0].strip()
    lines = []
    for line in normalized.split("\n"):
        compact = re.sub(r"\s+", " ", line).strip()
        if not compact:
            continue
        if compact.startswith("주식 ") and compact.count(" ") > 8:
            continue
        lines.append(compact)
    return "\n".join(lines[:8]).strip()


def normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) == 8 and value.isdigit():
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
    return value


def find_matches(text: str, mapping: dict[str, list[str]]) -> list[str]:
    found = []
    lowered = text.lower()
    for name, keywords in mapping.items():
        for keyword in keywords:
            normalized = keyword.strip()
            if not normalized:
                continue
            if normalized.isascii() and len(normalized) < 3:
                continue
            if normalized.lower() in lowered:
                found.append(name)
                break
    unique = []
    for item in found:
        if item not in unique:
            unique.append(item)
    return unique


def normalize_item(item: dict, sectors: dict, ib_aliases: dict, stocks: dict) -> dict:
    title = clean_title(item.get("title") or "")
    description = clean_description(item.get("description") or "")
    tags = item.get("tags") or []
    entity_text = " ".join([title, description]).strip()
    raw_text = " ".join([title, description, " ".join(tags)]).strip()
    matched_stocks = find_matches(entity_text, stocks)
    matched_ib = find_matches(entity_text, ib_aliases)
    matched_sectors = find_matches(entity_text, sectors)
    category = matched_sectors[0] if matched_sectors else ("ib_supply" if matched_ib else "long_term_pick")
    return {
        "video_id": item.get("id") or item.get("url") or "",
        "channel": item.get("channel") or "IBStock",
        "title": title,
        "description": description,
        "search_text": entity_text,
        "raw_text": raw_text,
        "source_url": item.get("webpage_url") or item.get("url"),
        "published_at": normalize_date(item.get("upload_date")),
        "views": item.get("view_count") or 0,
        "category": category,
        "stocks": matched_stocks,
        "ib_names": matched_ib,
        "sectors": matched_sectors,
        "normalized_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    payload = load_json(RAW_PATH)
    sectors = load_json(SECTOR_PATH)
    ib_aliases = load_json(IB_PATH)
    stocks = load_json(STOCKS_PATH)
    normalized = [
        normalize_item(item, sectors, ib_aliases, stocks)
        for item in payload.get("items", [])
    ]
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(
            {
                "source": str(RAW_PATH.name),
                "count": len(normalized),
                "items": normalized,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"normalized {len(normalized)} items")


if __name__ == "__main__":
    main()
