from app.core.database import get_connection


class DBService:
    def list_sectors(self) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT code, name, description, keywords_json
                FROM sectors
                ORDER BY name
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def list_ib_supply(self, limit: int = 20) -> list[dict]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT ib_name, stock_name, action, date, video_id
                FROM ib_supply
                ORDER BY date DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_stock_mentions(self, query: str, limit: int = 10) -> list[dict]:
        keyword = f"%{query}%"
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    m.stock_name,
                    m.sector,
                    m.ib_source,
                    m.mention_type,
                    m.confidence,
                    v.video_id,
                    v.title,
                    v.published_at,
                    v.views
                FROM stock_mentions m
                JOIN shorts_videos v ON v.video_id = m.video_id
                WHERE
                    m.stock_name LIKE ?
                    OR m.sector LIKE ?
                    OR m.ib_source LIKE ?
                    OR v.title LIKE ?
                ORDER BY v.published_at DESC, v.views DESC
                LIMIT ?
                """,
                (keyword, keyword, keyword, keyword, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def search_video_matches(self, query: str, limit: int = 10) -> list[dict]:
        keyword = f"%{query}%"
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    v.video_id,
                    v.title,
                    v.published_at,
                    v.views,
                    v.category,
                    v.source_url,
                    v.raw_text,
                    GROUP_CONCAT(DISTINCT m.stock_name) AS stocks_csv,
                    GROUP_CONCAT(DISTINCT m.ib_source) AS ib_sources_csv,
                    GROUP_CONCAT(DISTINCT m.sector) AS sectors_csv
                FROM shorts_videos v
                LEFT JOIN stock_mentions m ON m.video_id = v.video_id
                LEFT JOIN ib_supply s ON s.video_id = v.video_id
                WHERE
                    v.title LIKE ?
                    OR v.raw_text LIKE ?
                    OR m.stock_name LIKE ?
                    OR m.ib_source LIKE ?
                    OR m.sector LIKE ?
                    OR s.ib_name LIKE ?
                    OR s.stock_name LIKE ?
                GROUP BY v.video_id, v.title, v.published_at, v.views, v.category, v.source_url, v.raw_text
                ORDER BY v.published_at DESC, v.views DESC
                LIMIT ?
                """,
                (keyword, keyword, keyword, keyword, keyword, keyword, keyword, limit),
            ).fetchall()
        items = []
        for row in rows:
            item = dict(row)
            item["stocks"] = [value for value in (item.pop("stocks_csv") or "").split(",") if value]
            ib_values = [value for value in (item.pop("ib_sources_csv") or "").split(",") if value]
            sectors = [value for value in (item.pop("sectors_csv") or "").split(",") if value]
            item["ib_names"] = []
            for value in ib_values:
                for token in value.split(","):
                    token = token.strip()
                    if token and token not in item["ib_names"]:
                        item["ib_names"].append(token)
            item["sectors"] = []
            for token in sectors:
                token = token.strip()
                if token and token not in item["sectors"]:
                    item["sectors"].append(token)
            item["description"] = item.get("raw_text") or ""
            item["score"] = 1.0
            items.append(item)
        return items


db_service = DBService()
