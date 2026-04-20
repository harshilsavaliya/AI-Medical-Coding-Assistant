# Architecture

## Overview

The AI Medical Coding Assistant is a full-stack application that converts clinical text or uploaded medical images into ICD-10 suggestions. The backend handles extraction, OCR, mapping, and response formatting. The frontend provides a two-mode review interface for text input and file upload.

The current system is intentionally human-in-the-loop:

- the LLM extracts candidate conditions
- the curated CSV dataset remains the source of truth for returned ICD metadata
- the API surfaces reviewer metadata so a coder can see what mapped cleanly and what still needs review

## High-Level Flow

```text
Frontend
  |
  v
POST /predict or POST /predict-from-file
  |
  v
FastAPI route validation
  |
  v
PredictionService or FilePredictionService
  |
  v
EasyOCR extraction for uploaded images
  |
  v
DiagnosisExtractor
  |
  v
LangChain + OpenAI
  |
  v
ExtractedCondition list
  |
  v
IcdMapper + curated CSV dataset
  |
  v
PredictionResponse with codes + review metadata
```

## Backend Components

### API layer

- [backend/app/main.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/main.py) creates the FastAPI application
- [backend/app/routes/predict.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/routes/predict.py) exposes:
  - `POST /predict`
  - `POST /predict-from-file`

### Schema layer

- [backend/app/models/schemas.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/models/schemas.py) defines:
  - `PredictionRequest`
  - `CodePrediction`
  - `ExtractedConditionReview`
  - `PredictionResponse`

### Service layer

- [backend/app/services/prediction_service.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/prediction_service.py)
  - normalizes text
  - calls the extractor
  - calls the mapper
  - computes explanation and `review_status`
  - returns a review-friendly response
- [backend/app/services/file_prediction_service.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/file_prediction_service.py)
  - validates upload content
  - runs OCR with EasyOCR
  - forwards OCR text into the same prediction workflow

### AI and mapping layer

- [backend/ai/prompts/extractor.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/prompts/extractor.py)
  - sends the note to the model
  - parses JSON output
  - normalizes extracted condition records
- [backend/ai/mapping/icd_mapper.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/mapping/icd_mapper.py)
  - loads the ICD CSV dataset
  - matches extracted conditions against canonical names and aliases
  - deduplicates repeated final codes
  - preserves per-condition mapping metadata and unmatched conditions

### Data and configuration

- [backend/data/icd_codes.csv](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/data/icd_codes.csv) is the curated starter ICD dataset
- [backend/app/utils/config.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/utils/config.py) loads environment-backed settings such as:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL`
  - ICD dataset path
  - EasyOCR cache directories

## Frontend Components

- [frontend/src/App.tsx](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/App.tsx) owns:
  - the `Text Input` and `File Upload` tabs
  - submission state
  - API calls
  - result handoff to the shared result panel
- [frontend/src/components/ResultPanel.tsx](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/components/ResultPanel.tsx) renders:
  - ICD code cards
  - review-status badge
  - extracted-condition evidence cards
  - unmatched-condition review section
- [frontend/src/lib/api.ts](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/lib/api.ts) holds the typed fetch helpers
- [frontend/src/styles.css](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/styles.css) contains the dashboard UI styles

## Review Metadata Design

The current response model supports real review workflows better than a plain list of codes:

- `review_status = "auto_suggested"` when every extracted condition maps cleanly
- `review_status = "needs_review"` when some extracted conditions do not map or when no codes are returned
- `extracted_conditions` shows the model output plus `mapped_code` when available
- `unmatched_conditions` gives the reviewer a quick list of extracted terms that need manual follow-up

This keeps the system useful even when the curated ICD dataset is intentionally small.
