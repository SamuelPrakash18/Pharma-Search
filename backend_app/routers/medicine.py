from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import HealthResponse, MedicineDetailRequest, RecommendRequest, RecommendResponse, SearchRequest, SearchResponse
from ..services import format_detail_response, get_vector_search_service


router = APIRouter(prefix="/api", tags=["medicine"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    service = get_vector_search_service()
    return HealthResponse(status="ok", indexed_records=len(service.dataset.records))


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    service = get_vector_search_service()
    results = service.search(payload.query, top_k=payload.top_k)
    return SearchResponse(query=payload.query, results=results)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest) -> RecommendResponse:
    service = get_vector_search_service()
    results = service.recommend(payload.medicine_name, top_k=payload.top_k)
    return RecommendResponse(medicine_name=payload.medicine_name, results=results)


@router.post("/details")
def details(payload: MedicineDetailRequest):
    service = get_vector_search_service()
    record = service.details(payload.medicine_name)
    if record is None:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return format_detail_response(record)
