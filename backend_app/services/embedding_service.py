from __future__ import annotations

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ..preprocessing.data_loader import load_dataset


class MedicineEmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(embeddings, dtype=np.float32)

    def build_corpus_embeddings(self) -> np.ndarray:
        dataset = load_dataset()
        texts = [record.searchable_text for record in dataset.records]
        return self.embed_texts(texts)


@lru_cache(maxsize=1)
def get_embedding_service() -> MedicineEmbeddingService:
    return MedicineEmbeddingService()
