# Current Implementation Guide

This document describes the current implementation of the AI Medical Coding Assistant after the reviewer-metadata upgrade. The system supports direct clinical text analysis, image upload with OCR, ICD-10 mapping, and a frontend review workflow that highlights both matched and unmatched extracted conditions.

## Implementation Summary

The project currently provides:

- FastAPI endpoints for text and image-based prediction
- LangChain + OpenAI extraction of diagnosis-like conditions
- EasyOCR extraction for uploaded image files
- a curated ICD-10 CSV dataset used as the source of truth for mapped code metadata
- a mapper that returns both final ICD codes and condition-level review metadata
- a React frontend with shared results rendering for both text and file workflows

## End-To-End Flow

```text
Client
  |
  v
POST /predict or POST /predict-from-file
  |
  v
Request validation
  |
  v
PredictionService or FilePredictionService
  |
  v
OCR extraction for image uploads
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
IcdMapper + curated ICD CSV
  |
  v
PredictionResponse
  - codes
  - explanation
  - review_status
  - extracted_conditions
  - unmatched_conditions
```

## Current Project Structure

```text
backend/
|-- app/
|   |-- main.py
|   |-- models/
|   |   `-- schemas.py
|   |-- routes/
|   |   `-- predict.py
|   |-- services/
|   |   |-- file_prediction_service.py
|   |   `-- prediction_service.py
|   `-- utils/
|       `-- config.py
|-- ai/
|   |-- mapping/
|   |   `-- icd_mapper.py
|   `-- prompts/
|       `-- extractor.py
|-- data/
|   `-- icd_codes.csv
|-- .env.example
`-- requirements.txt

frontend/
|-- src/
|   |-- components/
|   |   |-- ResultPanel.tsx
|   |   |-- StatusBanner.tsx
|   |   `-- WorkflowCard.tsx
|   |-- lib/
|   |   `-- api.ts
|   |-- App.tsx
|   |-- main.tsx
|   |-- styles.css
|   `-- vite-env.d.ts
|-- .env.example
`-- package.json

docs/
|-- README.md
|-- Architecture.md
|-- API.md
`-- Development.md

tests/
|-- conftest.py
|-- test_file_prediction_service.py
|-- test_predict_api.py
|-- test_predict_file_api.py
`-- test_prediction_service.py
```

## Main Components

### 1. FastAPI app

File: [backend/app/main.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/main.py)

Responsibilities:

- creates the FastAPI application
- registers the prediction routes
- exposes a root endpoint for quick sanity checks

### 2. Routes

File: [backend/app/routes/predict.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/routes/predict.py)

Responsibilities:

- accepts `POST /predict`
- accepts `POST /predict-from-file`
- validates text requests through the request schema
- reads file uploads and forwards them into the file prediction service
- converts service-level failures into controlled HTTP responses

### 3. Request and response schema

File: [backend/app/models/schemas.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/models/schemas.py)

The current public response shape is:

```json
{
  "codes": [
    {
      "code": "E11",
      "description": "Type 2 diabetes mellitus",
      "confidence": 0.92
    }
  ],
  "explanation": "Mapped extracted conditions to ICD-10 codes for: Type 2 diabetes mellitus.",
  "review_status": "auto_suggested",
  "extracted_conditions": [
    {
      "name": "uncontrolled diabetes",
      "confidence": 0.92,
      "evidence": "uncontrolled diabetes",
      "mapped_code": "E11"
    }
  ],
  "unmatched_conditions": []
}
```

Schema highlights:

- `text` is normalized and must not be empty
- `confidence` values are constrained to `0.0` through `1.0`
- `mapped_code` is nullable when a condition is extracted but not mapped

### 4. Prediction service

File: [backend/app/services/prediction_service.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/prediction_service.py)

Responsibilities:

- normalizes text input
- calls the diagnosis extractor
- calls the ICD mapper
- builds explanation text
- determines whether the result is `auto_suggested` or `needs_review`
- returns the final API response

Current review-status behavior:

- `auto_suggested` when extracted conditions exist, codes are mapped, and no extracted conditions are left unmatched
- `needs_review` in all other cases

### 5. File prediction service

File: [backend/app/services/file_prediction_service.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/file_prediction_service.py)

Responsibilities:

- validates uploaded file content type and non-empty payload
- opens the uploaded image safely
- extracts OCR text with EasyOCR
- forwards OCR text into the same prediction service used by text input

Supported file types:

- `image/jpeg`
- `image/jpg`
- `image/png`

### 6. Diagnosis extraction layer

File: [backend/ai/prompts/extractor.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/prompts/extractor.py)

Responsibilities:

- defines the system prompt
- invokes the OpenAI model through LangChain
- requires JSON output in a fixed structure
- normalizes extracted conditions into Python objects

Expected extracted-condition shape:

```json
{
  "conditions": [
    {
      "name": "hypertension",
      "confidence": 0.88,
      "evidence": "hypertension"
    }
  ]
}
```

### 7. ICD mapping layer

File: [backend/ai/mapping/icd_mapper.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/mapping/icd_mapper.py)

Responsibilities:

- loads the curated ICD dataset from CSV
- matches extracted conditions against canonical names and aliases
- preserves per-condition mapping detail for reviewer visibility
- deduplicates repeated final ICD codes
- returns unmatched extracted conditions for manual review

Matching behavior:

- exact canonical-name match
- alias equality match
- simple partial alias containment

### 8. Frontend review workflow

Files:

- [frontend/src/App.tsx](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/App.tsx)
- [frontend/src/components/ResultPanel.tsx](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/frontend/src/components/ResultPanel.tsx)

Responsibilities:

- provides `Text Input` and `File Upload` tabs
- submits data to the appropriate backend endpoint
- renders a shared result panel for both workflows
- displays:
  - ICD code cards
  - explanation text
  - review-status badge
  - extracted-condition evidence cards
  - unmatched-condition warning section

## Worked Example

Input:

```text
Patient presents with uncontrolled diabetes and hypertension.
```

### Step 1. Request is validated

The request schema normalizes whitespace and rejects empty input.

### Step 2. The extractor returns candidate conditions

A typical normalized extractor result looks like:

```text
[
  ExtractedCondition(name="uncontrolled diabetes", confidence=0.92, evidence="uncontrolled diabetes"),
  ExtractedCondition(name="hypertension", confidence=0.88, evidence="hypertension")
]
```

### Step 3. The mapper checks the curated CSV dataset

Relevant dataset entries:

```text
E11,Type 2 diabetes mellitus,diabetes mellitus,diabetes|type 2 diabetes|uncontrolled diabetes
I10,Essential hypertension,hypertension,hypertension|high blood pressure
```

### Step 4. The service builds a review-friendly response

Final response:

```json
{
  "codes": [
    {
      "code": "E11",
      "description": "Type 2 diabetes mellitus",
      "confidence": 0.92
    },
    {
      "code": "I10",
      "description": "Essential hypertension",
      "confidence": 0.88
    }
  ],
  "explanation": "Mapped extracted conditions to ICD-10 codes for: Type 2 diabetes mellitus, Essential hypertension.",
  "review_status": "auto_suggested",
  "extracted_conditions": [
    {
      "name": "uncontrolled diabetes",
      "confidence": 0.92,
      "evidence": "uncontrolled diabetes",
      "mapped_code": "E11"
    },
    {
      "name": "hypertension",
      "confidence": 0.88,
      "evidence": "hypertension",
      "mapped_code": "I10"
    }
  ],
  "unmatched_conditions": []
}
```

## File Upload Workflow

The upload flow follows the same final prediction path after OCR:

```text
Image upload
-> file validation
-> OCR extraction
-> PredictionService
-> condition extraction
-> ICD mapping
-> reviewer-friendly API response
```

The frontend can render file-upload results without any separate result schema because `/predict-from-file` returns the same response contract as `/predict`.

## Configuration

File: [backend/app/utils/config.py](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/utils/config.py)

Supported settings:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `icd_dataset_path`
- EasyOCR model and network cache directories

Suggested backend environment file:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Suggested frontend environment file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Testing

Run backend tests:

```bash
python -m pytest
```

Run frontend build verification:

```bash
cd frontend
npm run build
```

Current test coverage includes:

- successful text and file prediction responses
- malformed request validation
- unsupported upload handling
- OCR empty-output and OCR failure handling
- deduplication of repeated mapped ICD codes
- unmatched-condition handling
- review-status behavior for both mapped-only and mixed-result cases

## Current Limitations

- the ICD dataset is intentionally small and not clinically complete
- confidence values are normalized but not clinically calibrated
- mapping logic is intentionally simple and may need stronger synonym support
- OCR is image-only in the current implementation
- PDF upload is not included yet
- no persistence, audit trail, or authentication has been added yet

## Related Documentation

- [README.md](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/README.md)
- [docs/README.md](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/docs/README.md)
- [docs/Architecture.md](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/docs/Architecture.md)
- [docs/API.md](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/docs/API.md)
- [docs/Development.md](/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/docs/Development.md)
