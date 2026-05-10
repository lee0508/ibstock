import hashlib
import json

import faiss
import httpx
import numpy as np

from app.core.config import settings


class FaissStore:
    def __init__(self) -> None:
        self.index_path = settings.faiss_dir / "index.faiss"
        self.metadata_path = settings.faiss_dir / "metadata.json"
        self.build_info_path = settings.faiss_dir / "build_info.json"
        self._index: faiss.Index | None = None
        self._metadata: list[dict] = []

    def _fallback_embedding(self, text: str, dim: int = 256) -> np.ndarray:
        vector = np.zeros(dim, dtype="float32")
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "little") % dim
            vector[slot] += 1.0
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector /= norm
        return vector

    async def embed_text(self, text: str) -> np.ndarray:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.ollama_host}/api/embeddings",
                    json={"model": settings.ollama_embed_model, "prompt": text},
                )
                response.raise_for_status()
                embedding = np.array(response.json().get("embedding", []), dtype="float32")
                if embedding.size:
                    norm = np.linalg.norm(embedding)
                    if norm > 0:
                        embedding /= norm
                    return embedding
        except Exception:
            pass
        return self._fallback_embedding(text)

    def load(self) -> bool:
        if not self.index_path.exists() or not self.metadata_path.exists():
            self._index = None
            self._metadata = []
            return False
        self._index = faiss.read_index(str(self.index_path))
        self._metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return True

    @property
    def loaded(self) -> bool:
        return self._index is not None and bool(self._metadata)

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        if not self.loaded and not self.load():
            return []
        if not self._index:
            return []
        query_vector = await self.embed_text(query)
        distances, indices = self._index.search(np.array([query_vector], dtype="float32"), limit)
        items = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            row = dict(self._metadata[idx])
            row["score"] = float(score)
            items.append(row)
        return items

    def info(self) -> dict:
        build_info = {}
        if self.build_info_path.exists():
            build_info = json.loads(self.build_info_path.read_text(encoding="utf-8"))
        return {
            "loaded": self.loaded or self.load(),
            "index_path": str(self.index_path),
            "metadata_path": str(self.metadata_path),
            "build": build_info,
        }


faiss_store = FaissStore()
