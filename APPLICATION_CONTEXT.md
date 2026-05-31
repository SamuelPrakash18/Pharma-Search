# Application Context - Drug Search Bot

## 1) Purpose

This application is a medicine intelligence assistant focused on retrieval.
It does not do conversational doctor chat in the active flow.
It supports:

1. Semantic medicine search from free text.
2. Similar medicine recommendation from a medicine name.
3. Direct medicine detail lookup.
4. Health/index visibility for runtime diagnostics.

## 2) Active Runtime Architecture

### Entrypoints

1. Backend process starts from `main.py`, which imports `app` from `backend_app.main`.
2. `backend/main.py` is the backend package entrypoint and proxies to `backend_app.main`.
3. `backend_app/main.py` builds a FastAPI app with CORS enabled.
4. Active router registration is medicine-only via `backend_app/routers/medicine.py`.
5. Frontend runtime is React/Vite using `frontend/src/App.jsx` and `frontend/src/styles.css`.
6. Optional standalone UI exists in `streamlit_app.py` and uses the same service layer.

### Active API surface

1. `GET /api/health`
2. `POST /api/search`
3. `POST /api/recommend`
4. `POST /api/details`

## 3) Minute-Detail Working Logic

### 3.1 Frontend logic (`src/App.jsx`)

1. UI state is split into four blocks:
  1. Search block: `query`, `topK`, `includeSideEffects`, `searchLoading`, `searchResults`, `searchError`, `searchTouched`.
  2. Details block: `medicineName`, `detailsLoading`, `detailsResult`, `detailsError`, `detailsTouched`.
  3. Recommendation block: `recommendName`, `recommendLoading`, `recommendResults`, `recommendError`, `recommendTouched`.
  4. Health block: `health`, `healthError`, `healthLoading`.
2. Health is fetched once on mount and can be refreshed from the hero action.
3. `parseResponseBody` reads text first, then attempts JSON parse.
  1. This allows backend plain-string errors to still be handled.
4. `parseApiError` maps error response into user-facing fallback text.
5. Quick chips prefill common search and medicine examples to speed up exploration.
6. Form guards (`canSearch`, `canDetails`, `canRecommend`) prevent duplicate or empty requests.
7. On submit:
  1. Each handler (`onSearch`, `onDetails`, `onRecommend`) sets loading state true.
  2. Sends POST with JSON body.
  3. Parses response.
  4. On success, updates result state.
  5. On failure, stores readable error and clears stale results.
  6. Always resets loading state in `finally`.
8. Search requests now include the optional `include_side_effects` flag.
9. Health status is shown as a live indicator and the indexed record count is surfaced in the hero.
10. `ResultCard` renders common record fields and optional detail extras:
  1. `name`
  2. `composition`
  3. `uses`
  4. `side_effects`
  5. optional `score`
  6. optional `explanation`
  7. optional `safety_note`

### 3.2 API router logic (`backend_app/routers/medicine.py`)

1. Router prefix is `/api`.
2. Every endpoint acquires service via `get_vector_search_service()`.
3. `GET /health`:
  1. Returns status `ok`.
  2. Returns `indexed_records = len(service.dataset.records)`.
4. `POST /search`:
  1. Accepts `SearchRequest` (`query`, `top_k`, optional flag).
  2. Calls `service.search(query, top_k)`.
  3. Returns `SearchResponse`.
5. `POST /recommend`:
  1. Accepts `RecommendRequest` (`medicine_name`, `top_k`).
  2. Calls `service.recommend(medicine_name, top_k)`.
  3. Returns `RecommendResponse`.
6. `POST /details`:
  1. Accepts `MedicineDetailRequest` (`medicine_name`).
  2. Calls `service.details(medicine_name)`.
  3. If no match, throws HTTP 404.
  4. Else converts record through `format_detail_response`.

### 3.3 Service lifecycle (`backend_app/services/vector_search.py`)

1. `get_vector_search_service()` is LRU-cached (`maxsize=1`).
  1. Only one service instance is constructed per process.
2. Constructor sequence:
  1. Ensure artifact folder exists (`data/`).
  2. Load or build dataset metadata.
  3. Load or build corpus embeddings.
  4. Load or build FAISS index.
3. Dataset load/build:
  1. If `data/medicine_records.json` exists, read and model-validate records.
  2. Else load from Excel via data loader and persist JSON metadata.
4. Embedding load/build:
  1. If `data/medicine_embeddings.npy` exists, load ndarray.
  2. Else embed corpus text and save `.npy`.
5. Index load/build:
  1. If `data/medicine.index` exists, load FAISS index from disk.
  2. Else build `IndexFlatIP` with embedding dimension.
  3. Add vectors and save index file.
6. Search execution:
  1. Encode query text with normalized embedding.
  2. Perform `index.search(query_embedding, top_k)`.
  3. Map each hit index to medicine record.
  4. Build `MedicineSearchResult` with explanation text.
7. Recommendation execution:
  1. Try exact-name match (case-insensitive), then substring fallback.
  2. If target not found, fall back to plain semantic search on input text.
  3. If target found, search using target `searchable_text`.
  4. Request `top_k + 1`, then remove self-match by name.
8. Details execution:
  1. Reuses `_find_record` matching logic.

### 3.4 Embedding logic (`backend_app/services/embedding_service.py`)

1. Uses model `sentence-transformers/all-MiniLM-L6-v2` by default.
2. Text encoding uses `normalize_embeddings=True`.
  1. This enables cosine-similarity-like behavior when used with inner product.
3. Embeddings are returned as `float32` numpy arrays (required by FAISS best path).
4. Corpus embeddings are generated from each record's `searchable_text`.

### 3.5 Data loader logic (`backend_app/preprocessing/data_loader.py`)

1. Reads source file `medic.xlsx` via pandas.
2. For each row, extracts these columns:
  1. `NAME`
  2. `COMPOSITION`
  3. `USES`
  4. `SIDE_EFFECTS`
  5. `IMAGE_URL`
3. Normalization steps:
  1. Collapse extra whitespace.
  2. Lowercase normalized fields.
  3. Composition normalization replaces ` + ` with ` plus ` and unfolds bracket fragments.
4. Dosage extraction:
  1. Regex captures numeric dose with units (`mg`, `mcg`, `g`, `ml`, `iu`, `unit`, `ug`, `µg`).
  2. Converts numeric part to float list.
5. Builds `searchable_text` by concatenating:
  1. lowercased name
  2. normalized composition
  3. normalized uses
  4. normalized side effects
  5. dosage value tokens (if present)
6. Dataset load function is LRU-cached (`maxsize=1`) for process-level reuse.

### 3.6 Response shaping (`backend_app/services/response_generator.py`)

1. Search explanations are generated per result to describe why it matched.
2. Detail response injects a standard safety note.
3. This module is where user-visible wording should be changed, not retrieval core.

## 4) Data and Artifacts

Runtime artifacts in `data/`:

1. `medicine_records.json`: structured metadata snapshot used for quick startup.
2. `medicine_embeddings.npy`: cached corpus embeddings.
3. `medicine.index`: FAISS index for nearest-neighbor search.

If these files are deleted, service rebuilds them automatically from source data.

## 5) Exact Request/Response Contracts

### `POST /api/search`

Request:

1. `query: str`
2. `top_k: int` default 5, bounds in model validation
3. `include_side_effects: bool` currently accepted but not actively branching retrieval logic

Response:

1. `query: str`
2. `results: list[MedicineSearchResult]`

### `POST /api/recommend`

Request:

1. `medicine_name: str`
2. `top_k: int` default 5

Response:

1. `medicine_name: str`
2. `results: list[MedicineSearchResult]`

### `POST /api/details`

Request:

1. `medicine_name: str`

Response:

1. Detail payload fields from `MedicineDetailResponse`
2. HTTP 404 with `Medicine not found` if no match

## 6) Performance Characteristics

1. First request may be slower if artifacts need to be built.
2. Later requests are faster due to:
  1. process-level cached service
  2. on-disk cached embeddings/index
3. Search complexity is FAISS nearest-neighbor over in-memory vectors.

## 7) Feature Integration Rules

1. Keep existing endpoints backward-compatible unless versioning is introduced.
2. Update `backend_app/models.py` first when changing payload shape.
3. For ranking or retrieval changes, update:
  1. `backend_app/services/vector_search.py`
  2. `backend_app/services/embedding_service.py` (if embedding strategy changes)
  3. `backend_app/services/response_generator.py` (if explanation text changes)
4. If source schema changes, update loader logic and regenerate artifacts.
5. Keep frontend field usage aligned with backend response fields.
6. Reflect all behavior changes in `README.md` and this file.

## 8) Legacy Modules Notice

Legacy chat/auth/database files exist in repository history and folders.
They are not part of the active drug-search app routing path today.

## 9) Troubleshooting Checklist

1. Empty results for all queries:
  1. Confirm `medic.xlsx` exists and has expected columns.
  2. Remove stale artifacts in `data/` and restart to force rebuild.
2. Backend starts but frontend shows fetch errors:
  1. Confirm backend is on port 8000.
  2. Confirm frontend uses correct base URL/proxy setup.
3. `details` returns 404 for obvious medicine name:
  1. Check exact naming in dataset.
  2. Verify loader normalization did not strip meaningful tokens.
4. Slow first run:
  1. Expected when model/index artifacts are not present.
  2. Subsequent calls should improve after cache warmup.
