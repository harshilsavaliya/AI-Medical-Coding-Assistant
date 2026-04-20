# Development Guide

## Prerequisites

- Python 3.11+ recommended
- Node.js 18+ recommended
- npm
- An OpenAI API key for live diagnosis extraction

## Backend Setup

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Create the environment file:

```bash
copy backend\.env.example backend\.env
```

Set at least:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Run the backend:

```bash
uvicorn app.main:app --reload --app-dir backend
```

## Frontend Setup

Install dependencies:

```bash
cd frontend
npm install
```

Create the frontend environment file:

```bash
copy .env.example .env
```

Default API target:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run the frontend:

```bash
npm run dev
```

## Verification

Run backend tests:

```bash
python -m pytest
```

Build the frontend:

```bash
npm run build
```

## What The Current Tests Cover

- successful `POST /predict` responses
- successful `POST /predict-from-file` responses
- request validation failures
- unsupported upload handling
- OCR empty-output and OCR failure handling
- known-condition mapping
- duplicate-code deduplication
- unmatched-condition handling
- reviewer-metadata response fields

## Common Notes

- EasyOCR downloads and caches model assets in the configured backend cache directories
- the project currently uses a curated starter ICD dataset rather than a clinically complete coding catalog
- the frontend build expects Vite type declarations, which are already included in `frontend/src/vite-env.d.ts`

## Suggested Next Improvements

- replace the current basic file input with a more polished upload/dropzone component
- expand the curated ICD dataset and synonym coverage
- add health, readiness, and observability endpoints
- add persistence or audit-trail support if you want to keep reviewer decisions
