from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..models import MedicineRecord


ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = ROOT_DIR / "medic.xlsx"


def _normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_dosage_values(text: str) -> list[float]:
    values: list[float] = []
    pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|units?|µg|ug)", re.IGNORECASE)
    for match in pattern.finditer(text):
        try:
            values.append(float(match.group(1)))
        except ValueError:
            continue
    return values


def _normalize_composition(text: str) -> str:
    cleaned = text.lower()
    cleaned = cleaned.replace(" + ", " plus ")
    cleaned = re.sub(r"\(([^)]+)\)", r" \1 ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


@dataclass(frozen=True)
class MedicineDataset:
    records: list[MedicineRecord]

    @classmethod
    def load(cls, dataset_path: Path | None = None) -> "MedicineDataset":
        path = dataset_path or DATASET_PATH
        frame = pd.read_excel(path)
        records: list[MedicineRecord] = []
        for _, row in frame.iterrows():
            name = _normalize_text(row.get("NAME"))
            composition = _normalize_text(row.get("COMPOSITION"))
            uses = _normalize_text(row.get("USES"))
            side_effects = _normalize_text(row.get("SIDE_EFFECTS"))
            image_url = _normalize_text(row.get("IMAGE_URL"))
            dosage_values = _extract_dosage_values(composition)
            normalized_composition = _normalize_composition(composition)
            normalized_uses = uses.lower()
            normalized_side_effects = side_effects.lower()
            searchable_text = " ".join(
                [
                    name.lower(),
                    normalized_composition,
                    normalized_uses,
                    normalized_side_effects,
                    "dosage " + " ".join(str(value) for value in dosage_values) if dosage_values else "",
                ]
            ).strip()
            records.append(
                MedicineRecord(
                    name=name,
                    composition=composition,
                    uses=uses,
                    side_effects=side_effects,
                    image_url=image_url,
                    dosage_values=dosage_values,
                    normalized_composition=normalized_composition,
                    normalized_uses=normalized_uses,
                    normalized_side_effects=normalized_side_effects,
                    searchable_text=searchable_text,
                )
            )
        return cls(records=records)


@lru_cache(maxsize=1)
def load_dataset() -> MedicineDataset:
    return MedicineDataset.load()
