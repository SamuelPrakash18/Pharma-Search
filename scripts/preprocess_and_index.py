from __future__ import annotations

from backend_app.services.vector_search import get_vector_search_service


if __name__ == "__main__":
    service = get_vector_search_service()
    print(f"Indexed {len(service.dataset.records)} medicine records.")
