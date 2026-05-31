from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import faiss
import numpy as np

from ..models import MedicineRecord, MedicineSearchResult
from ..preprocessing.data_loader import load_dataset
from .embedding_service import get_embedding_service
from .response_generator import format_search_explanation


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ARTIFACT_DIR = ROOT_DIR / "data"
INDEX_PATH = ARTIFACT_DIR / "medicine.index"
METADATA_PATH = ARTIFACT_DIR / "medicine_records.json"


class MedicineVectorSearchService:
    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.dataset = self._load_or_build_dataset()
        self.embedding_service = get_embedding_service()
        self.embeddings = self._load_or_build_embeddings()
        self.index = self._load_or_build_index(self.embeddings)

    def _build_index(self, embeddings: np.ndarray) -> faiss.Index:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index

    def _load_or_build_dataset(self):
        if METADATA_PATH.exists():
            payload = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
            from ..preprocessing.data_loader import MedicineDataset

            return MedicineDataset(records=[MedicineRecord.model_validate(item) for item in payload])
        dataset = load_dataset()
        METADATA_PATH.write_text(
            json.dumps([record.model_dump() for record in dataset.records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return dataset

    def _load_or_build_embeddings(self) -> np.ndarray:
        embeddings_path = ARTIFACT_DIR / "medicine_embeddings.npy"
        if embeddings_path.exists():
            return np.load(embeddings_path)
        embeddings = self.embedding_service.build_corpus_embeddings()
        np.save(embeddings_path, embeddings)
        return embeddings

    def _load_or_build_index(self, embeddings: np.ndarray) -> faiss.Index:
        if INDEX_PATH.exists():
            return faiss.read_index(str(INDEX_PATH))
        index = self._build_index(embeddings)
        faiss.write_index(index, str(INDEX_PATH))
        return index

    def search(self, query: str, top_k: int = 5) -> list[MedicineSearchResult]:
        query_embedding = self.embedding_service.embed_texts([query])
        scores, indices = self.index.search(query_embedding, top_k)
        results: list[MedicineSearchResult] = []
        for score, index in zip(scores[0], indices[0], strict=False):
            if index < 0:
                continue
            record = self.dataset.records[index]
            results.append(self._to_result(record, float(score), query))
        return results

    def recommend(self, medicine_name: str, top_k: int = 5) -> list[MedicineSearchResult]:
        target = self._find_record(medicine_name)
        if target is None:
            return self.search(medicine_name, top_k=top_k)
        results = self.search(target.searchable_text, top_k=top_k + 1)
        return [result for result in results if result.name.lower() != target.name.lower()][:top_k]

    def details(self, medicine_name: str) -> MedicineRecord | None:
        return self._find_record(medicine_name)

    def _find_record(self, medicine_name: str) -> MedicineRecord | None:
        target = medicine_name.strip().lower()
        for record in self.dataset.records:
            if record.name.lower() == target:
                return record
        for record in self.dataset.records:
            if target in record.name.lower():
                return record
        return None

    def _to_result(self, record: MedicineRecord, score: float, query: str) -> MedicineSearchResult:
        return MedicineSearchResult(
            name=record.name,
            composition=record.composition,
            uses=record.uses,
            side_effects=record.side_effects,
            image_url=record.image_url,
            score=score,
            dosage_values=record.dosage_values,
            explanation=format_search_explanation(query=query, record=record, score=score),
        )


@lru_cache(maxsize=1)
def get_vector_search_service() -> MedicineVectorSearchService:
    return MedicineVectorSearchService()
