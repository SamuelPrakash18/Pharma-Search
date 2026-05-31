from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    include_side_effects: bool = True


class RecommendRequest(BaseModel):
    medicine_name: str
    top_k: int = Field(default=5, ge=1, le=20)


class MedicineDetailRequest(BaseModel):
    medicine_name: str


class MedicineRecord(BaseModel):
    name: str
    composition: str
    uses: str
    side_effects: str
    image_url: str = ""
    dosage_values: list[float] = Field(default_factory=list)
    normalized_composition: str = ""
    normalized_uses: str = ""
    normalized_side_effects: str = ""
    searchable_text: str = ""


class MedicineSearchResult(BaseModel):
    name: str
    composition: str
    uses: str
    side_effects: str
    image_url: str = ""
    score: float
    dosage_values: list[float] = Field(default_factory=list)
    explanation: str


class MedicineDetailResponse(BaseModel):
    name: str
    composition: str
    uses: str
    side_effects: str
    image_url: str = ""
    dosage_values: list[float] = Field(default_factory=list)
    safety_note: str


class SearchResponse(BaseModel):
    query: str
    results: list[MedicineSearchResult]


class RecommendResponse(BaseModel):
    medicine_name: str
    results: list[MedicineSearchResult]


class HealthResponse(BaseModel):
    status: str
    indexed_records: int


@dataclass(frozen=True)
class IndexedMedicine:
    record: MedicineRecord
    embedding_index: int
