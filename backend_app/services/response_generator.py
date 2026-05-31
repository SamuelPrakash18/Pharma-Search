from __future__ import annotations

from ..models import MedicineDetailResponse, MedicineRecord


def format_search_explanation(query: str, record: MedicineRecord, score: float) -> str:
    reasons: list[str] = []
    if query.strip().lower() in record.name.lower():
        reasons.append("name match")
    if record.dosage_values:
        reasons.append(f"dosage values: {', '.join(str(value) for value in record.dosage_values)}")
    if record.normalized_uses:
        reasons.append("usage aligned")
    if record.normalized_side_effects:
        reasons.append("side effect profile considered")
    reason_text = "; ".join(reasons) if reasons else "semantic similarity"
    return f"Matched by {reason_text}. Retrieval score {score:.3f}."


def format_detail_response(record: MedicineRecord) -> MedicineDetailResponse:
    safety_note = "Use only as prescribed by a qualified clinician. Verify allergies, dosage, and interactions before use."
    return MedicineDetailResponse(
        name=record.name,
        composition=record.composition,
        uses=record.uses,
        side_effects=record.side_effects,
        image_url=record.image_url,
        dosage_values=record.dosage_values,
        safety_note=safety_note,
    )
