import sqlite3

from app.core.config import settings


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
    confidence REAL DEFAULT 0.5,
    FOREIGN KEY (video_id) REFERENCES shorts_videos(video_id)
);

CREATE TABLE IF NOT EXISTS ib_supply (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    ib_name TEXT NOT NULL,
    stock_name TEXT,
    action TEXT DEFAULT 'watch',
    date TEXT,
    FOREIGN KEY (video_id) REFERENCES shorts_videos(video_id)
);

CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT UNIQUE NOT NULL,
    description TEXT,
    keywords_json TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    settings.sqlite_file.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.sqlite_file)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()


def database_exists() -> bool:
    return settings.sqlite_file.exists()
