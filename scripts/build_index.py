import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.config import settings
from app.services.faiss_store import FaissStore


INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "shorts_normalized.json"


def load_documents() -> list[dict]:
    payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    documents = []
    for item in payload.get("items", []):
        searchable_text = " ".join(
            [
                item.get("title") or "",
                item.get("description") or "",
                item.get("search_text") or "",
                " ".join(item.get("stocks") or []),
                " ".join(item.get("ib_names") or []),
                " ".join(item.get("sectors") or []),
            ]
        ).strip()
        documents.append(
            {
                "video_id": item.get("video_id"),
                "title": item.get("title"),
                "published_at": item.get("published_at"),
                "views": item.get("views"),
                "category": item.get("category"),
                "stocks": item.get("stocks") or [],
                "ib_names": item.get("ib_names") or [],
                "sectors": item.get("sectors") or [],
                "source_url": item.get("source_url"),
                "searchable_text": searchable_text,
            }
        )
    return documents


async def build() -> None:
    settings.faiss_dir.mkdir(parents=True, exist_ok=True)
    store = FaissStore()
    documents = load_documents()
    vectors = []
    metadata = []
    for document in documents:
        vector = await store.embed_text(document["searchable_text"])
        vectors.append(vector)
        metadata.append(document)
    if not vectors:
        raise RuntimeError("No documents available for indexing.")
    matrix = np.vstack(vectors).astype("float32")
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, str(settings.faiss_dir / "index.faiss"))
    (settings.faiss_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (settings.faiss_dir / "build_info.json").write_text(
        json.dumps(
            {
                "built_at": datetime.now(timezone.utc).isoformat(),
                "document_count": len(metadata),
                "dimension": int(matrix.shape[1]),
                "embedding_model": settings.ollama_embed_model,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"built faiss index with {len(metadata)} documents")


if __name__ == "__main__":
    asyncio.run(build())
