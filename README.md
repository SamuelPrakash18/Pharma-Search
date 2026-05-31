# HBT - Drug Search Bot (Vite + FastAPI)

This project is a drug-focused search and recommendation application.
It provides semantic medicine search, similar-drug recommendations, and medicine detail lookup.

## What This App Does

- Search medicines by natural language query (`/api/search`)
- Recommend similar medicines for a given medicine name (`/api/recommend`)
- Get structured medicine details (`/api/details`)
- Check backend indexing status (`/api/health`)

## Stack

- Frontend: Vite + React 18 + custom glassmorphism UI in `frontend/`
- Backend: FastAPI + Uvicorn in `backend/`
- NLP/Vector Search: sentence-transformers + FAISS
- Optional UI: Streamlit app for quick testing (`streamlit_app.py`)

## Requirements

- Python 3.10+
- Node.js 18+

## Install

Backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Frontend dependencies:

```bash
cd frontend
npm install
```

## Run

Start FastAPI backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Start Vite frontend:

```bash
cd frontend
npm run dev
```

Frontend URL is typically `http://localhost:5173`.

Optional Streamlit interface:

```bash
streamlit run streamlit_app.py
```

## API Endpoints

- `GET /api/health`
- `POST /api/search`
- `POST /api/recommend`
- `POST /api/details`

### Request/Response Shapes

`POST /api/search` request:

- `query: string`
- `top_k?: number` (default 5)
- `include_side_effects?: boolean`

`POST /api/search` response:

- `query: string`
- `results: MedicineSearchResult[]`

`POST /api/recommend` request:

- `medicine_name: string`
- `top_k?: number` (default 5)

`POST /api/details` request:

- `medicine_name: string`

## Quick Verification

1. Start backend and frontend in separate terminals.
2. Open `http://localhost:5173`.
3. Run these flows:
   - Search by query
   - Get medicine details
   - Get similar recommendations
4. Confirm each section returns expected data.

Manual API checks:

```bash
curl http://localhost:8000/api/health
```

```bash
curl -X POST http://localhost:8000/api/search -H "Content-Type: application/json" -d "{\"query\":\"fever medicine\",\"top_k\":5}"
```

```bash
curl -X POST http://localhost:8000/api/recommend -H "Content-Type: application/json" -d "{\"medicine_name\":\"Azithral 500 Tablet\",\"top_k\":5}"
```

```bash
curl -X POST http://localhost:8000/api/details -H "Content-Type: application/json" -d "{\"medicine_name\":\"Augmentin 625 Duo Tablet\"}"
```

## Project Notes

- Backend currently includes the medicine router as the active API surface.
- Dataset and embeddings are loaded from `data/` and indexed for vector search.
- Use `scripts/preprocess_and_index.py` to regenerate embeddings/index if source data changes.
- This repo also contains legacy chat/auth files from earlier iterations; they are not part of the active drug-search workflow.
