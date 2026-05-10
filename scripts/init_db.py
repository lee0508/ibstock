import json
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "db" / "ibstock.db"
NORMALIZED_PATH = PROJECT_ROOT / "data" / "processed" / "shorts_normalized.json"
SECTOR_PATH = PROJECT_ROOT / "data" / "reference" / "sector_keywords.json"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS shorts_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    channel TEXT NOT NULL,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    source_url TEXT,
    published_at TEXT,
    views INTEGER DEFAULT 0,
    category TEXT,
    collected_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stock_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    stock_name TEXT NOT NULL,
    sector TEXT,
    ib_source TEXT,
    mention_type TEXT DEFAULT 'watch',
    confidence REAL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS ib_supply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    ib_name TEXT NOT NULL,
    stock_name TEXT,
    action TEXT DEFAULT 'watch',
    date TEXT
);

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL,
    description TEXT,
    keywords_json TEXT NOT NULL
);
"""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def guess_sector_name(item: dict) -> str | None:
    sectors = item.get("sectors") or []
    return sectors[0] if sectors else None


def seed_sectors(connection: sqlite3.Connection) -> None:
    sectors = load_json(SECTOR_PATH)
    for code, keywords in sectors.items():
        connection.execute(
            """
            INSERT INTO sectors (name, code, description, keywords_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
                name = excluded.name,
                description = excluded.description,
                keywords_json = excluded.keywords_json
            """,
            (code, code, f"{code} sector", json.dumps(keywords, ensure_ascii=False)),
        )


def seed_normalized_items(connection: sqlite3.Connection) -> None:
    payload = load_json(NORMALIZED_PATH)
    video_ids = [item["video_id"] for item in payload.get("items", [])]

    if video_ids:
        placeholders = ",".join("?" for _ in video_ids)
        connection.execute(
            f"DELETE FROM stock_mentions WHERE video_id NOT IN ({placeholders})",
            video_ids,
        )
        connection.execute(
            f"DELETE FROM ib_supply WHERE video_id NOT IN ({placeholders})",
            video_ids,
        )
        connection.execute(
            f"DELETE FROM shorts_videos WHERE video_id NOT IN ({placeholders})",
            video_ids,
        )

    for item in payload.get("items", []):
        connection.execute(
            """
            INSERT INTO shorts_videos (
                video_id, channel, title, raw_text, source_url, published_at, views, category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                channel = excluded.channel,
                title = excluded.title,
                raw_text = excluded.raw_text,
                source_url = excluded.source_url,
                published_at = excluded.published_at,
                views = excluded.views,
                category = excluded.category
            """,
            (
                item["video_id"],
                item["channel"],
                item["title"],
                item["raw_text"],
                item["source_url"],
                item["published_at"],
                item["views"],
                item["category"],
            ),
        )

        connection.execute("DELETE FROM stock_mentions WHERE video_id = ?", (item["video_id"],))
        connection.execute("DELETE FROM ib_supply WHERE video_id = ?", (item["video_id"],))

        for stock_name in item.get("stocks", []):
            connection.execute(
                """
                INSERT INTO stock_mentions (
                    video_id, stock_name, sector, ib_source, mention_type, confidence
                )
                VALUES (?, ?, ?, ?, 'watch', 0.7)
                """,
                (
                    item["video_id"],
                    stock_name,
                    guess_sector_name(item),
                    ",".join(item.get("ib_names", [])),
                ),
            )

        for ib_name in item.get("ib_names", []):
            for stock_name in item.get("stocks", []) or [None]:
                connection.execute(
                    """
                    INSERT INTO ib_supply (video_id, ib_name, stock_name, action, date)
                    VALUES (?, ?, ?, 'watch', ?)
                    """,
                    (item["video_id"], ib_name, stock_name, item["published_at"]),
                )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA_SQL)
        seed_sectors(connection)
        seed_normalized_items(connection)
        connection.commit()
    print(f"seeded database at {DB_PATH}")


if __name__ == "__main__":
    main()
