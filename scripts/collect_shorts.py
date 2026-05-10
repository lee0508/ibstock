import json
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHANNEL_URL = "https://www.youtube.com/@Grandpa_Investor_Ib/shorts"


def collect_playlist_entries(limit: int = 50) -> list[dict]:
    options = {
        "extract_flat": True,
        "skip_download": True,
        "quiet": True,
        "playlistend": limit,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.extract_info(CHANNEL_URL, download=False)
    return result.get("entries", [])


def collect_video_detail(url: str) -> dict:
    options = {
        "skip_download": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        result = ydl.extract_info(url, download=False)
    return result


def collect_shorts(limit: int = 50) -> list[dict]:
    entries = collect_playlist_entries(limit=limit)
    items = []
    for entry in entries:
        detail_url = entry.get("url")
        if not detail_url:
            continue
        detail = collect_video_detail(detail_url)
        items.append(
            {
                "id": detail.get("id") or entry.get("id"),
                "title": detail.get("title") or entry.get("title"),
                "description": detail.get("description") or "",
                "tags": detail.get("tags") or [],
                "channel": detail.get("channel") or detail.get("uploader") or "",
                "view_count": detail.get("view_count") or entry.get("view_count") or 0,
                "upload_date": detail.get("upload_date"),
                "timestamp": detail.get("timestamp"),
                "webpage_url": detail.get("webpage_url") or detail_url,
                "thumbnail": detail.get("thumbnail"),
            }
        )
    return items


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    items = collect_shorts()
    payload = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "channel_url": CHANNEL_URL,
        "count": len(items),
        "items": items,
    }
    output_path = RAW_DIR / "shorts_latest.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {len(items)} items to {output_path}")


if __name__ == "__main__":
    main()
