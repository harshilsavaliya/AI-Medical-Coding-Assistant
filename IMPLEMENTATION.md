# Phase 1 Implementation Guide

This document explains the current implementation of the AI Medical Coding Assistant, including text-based prediction, image upload with OCR, and the unified frontend workflow.

## Overview

The current implementation focuses on:

- FastAPI APIs for direct text prediction and file upload prediction
- LangChain + OpenAI for extracting likely medical conditions
- EasyOCR for extracting text from uploaded image files
- A curated ICD-10 dataset used as the source of truth for returned code metadata
- A mapping and normalization layer that converts extracted conditions into a stable API response
- A React frontend with `Text Input` and `File Upload` tabs

## Current Request Flow

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
Text prediction service or file prediction service
  |
  v
OCR extraction when file upload is used
  |
  v
PredictionService
  |
  v
DiagnosisExtractor
  |
  v
LangChain + OpenAI
  |
  v
Extracted conditions
  |
  v
IcdMapper + curated CSV dataset
  |
  v
Normalized API response
```

## Project Structure

```text
backend/
|-- app/
|   |-- main.py
|   |-- models/
|   |   `-- schemas.py
|   |-- routes/
|   |   `-- predict.py
|   |-- services/
|   |   `-- file_prediction_service.py
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

tests/
|-- conftest.py
|-- test_predict_api.py
`-- test_prediction_service.py

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
|   `-- styles.css
|-- .env.example
`-- package.json
```

## Main Components

### 1. FastAPI App

File: [backend/app/main.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/main.py)

Responsibilities:

- Creates the FastAPI application
- Registers the prediction route
- Exposes a small root endpoint for quick sanity checks

### 2. API Route

File: [backend/app/routes/predict.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/routes/predict.py)

Responsibilities:

- Accepts `POST /predict`
- Accepts `POST /predict-from-file`
- Validates input using the request schema
- Calls the prediction service
- Calls the OCR file service for image uploads
- Converts service failures into controlled HTTP responses

### 3. Request and Response Schemas

File: [backend/app/models/schemas.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/models/schemas.py)

Current API contract:

Request:

```json
{
  "text": "Patient presents with uncontrolled diabetes and hypertension."
}
```

Response:

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
  "explanation": "Mapped extracted conditions to ICD-10 codes for: Type 2 diabetes mellitus, Essential hypertension."
}
```

File upload endpoint:

- `POST /predict-from-file`
- request format: multipart form upload with a single `file` field
- supported types: `image/jpg`, `image/jpeg`, `image/png`
- response format: same as the text endpoint

Validation rules:

- `text` is required
- `text` is whitespace-normalized before processing
- empty text is rejected
- `confidence` is constrained to the `0.0` to `1.0` range

### 4. Prediction Service

File: [backend/app/services/prediction_service.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/prediction_service.py)

Responsibilities:

- Normalizes the input text
- Calls the extraction layer
- Passes extracted conditions into the ICD mapper
- Builds the final explanation string
- Returns a response object matching the public API schema

This file contains the main orchestration logic for Phase 1.

### 5. File Prediction Service

File: [backend/app/services/file_prediction_service.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/file_prediction_service.py)

Responsibilities:

- Validates uploaded image type and content
- Reads the uploaded file into memory
- Runs OCR extraction through EasyOCR
- Forwards extracted text into the existing prediction service
- Returns the same response schema used by direct text submissions

This keeps OCR-specific logic separate from the main text prediction service.

### 6. Diagnosis Extraction Layer

File: [backend/ai/prompts/extractor.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/prompts/extractor.py)

Responsibilities:

- Defines the system prompt for the LLM
- Calls the OpenAI chat model through LangChain
- Requests structured JSON output
- Parses and normalizes extracted conditions into Python objects

Current extraction shape:

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

Important implementation detail:

- The LLM suggests candidate conditions
- The backend still owns normalization and final response formatting
- The curated ICD dataset remains the source of truth for returned code metadata

### 7. ICD Mapping Layer

File: [backend/ai/mapping/icd_mapper.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/mapping/icd_mapper.py)

Responsibilities:

- Loads the curated ICD dataset from CSV
- Matches extracted condition names against canonical names and aliases
- Deduplicates repeated ICD codes
- Returns normalized code entries used by the service layer

Matching behavior:

- exact canonical name match
- alias match
- partial alias containment for simple v1 flexibility

### 8. Curated Dataset

File: [backend/data/icd_codes.csv](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/data/icd_codes.csv)

The dataset currently includes a small set of common conditions for Phase 1, including:

- diabetes
- hypertension
- asthma
- chronic cough
- upper respiratory infection

CSV columns:

- `code`
- `description`
- `canonical_name`
- `aliases`

The `aliases` column uses pipe-separated values such as:

```text
diabetes|type 2 diabetes|uncontrolled diabetes
```

## File Upload Example

This example shows how the backend generates output for an uploaded image containing medical text.

### Step 1. Client uploads an image

The frontend sends a multipart request to `POST /predict-from-file` with one file field.

Example:

- file name: `note.png`
- content type: `image/png`

### Step 2. Backend validates the file

The file prediction service checks:

- the file is not empty
- the content type is supported
- the image can be opened successfully

If validation fails, the API returns a controlled error instead of a traceback.

### Step 3. OCR extracts readable text

EasyOCR reads the image and returns text fragments.

Example OCR output:

```text
["Patient presents with uncontrolled diabetes and hypertension"]
```

The service joins those segments into a single string:

```text
Patient presents with uncontrolled diabetes and hypertension
```

### Step 4. Extracted text enters the same prediction pipeline

After OCR, the backend reuses the existing text prediction flow:

```text
Extracted OCR text
-> PredictionService
-> LLM diagnosis extraction
-> CSV-based ICD mapping
-> normalized API response
```

### Step 5. Final output matches the text endpoint

The upload endpoint returns the same response shape as `POST /predict`, which lets the frontend render both workflows in one shared results panel.

## Worked Example

This example shows how the backend generates output for the following input:

```text
Patient presents with uncontrolled diabetes and hypertension.
```

### Step 1. Client sends request

The frontend or API client sends this JSON body to `POST /predict`:

```json
{
  "text": "Patient presents with uncontrolled diabetes and hypertension."
}
```

### Step 2. FastAPI validates the request

The request is validated by [backend/app/models/schemas.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/models/schemas.py).

What happens here:

- `text` must exist
- extra whitespace is normalized
- empty text would be rejected with a validation error

For this example, the normalized text remains:

```text
Patient presents with uncontrolled diabetes and hypertension.
```

### Step 3. Route calls the prediction service

The route in [backend/app/routes/predict.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/routes/predict.py) calls `PredictionService.predict(...)`.

At this point:

- the API layer stops handling transport details
- the service layer takes over the actual coding workflow

### Step 4. Prediction service prepares the text

Inside [backend/app/services/prediction_service.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/prediction_service.py):

- the text is normalized again for safety
- the service sends the normalized note to the extraction layer

Service input:

```text
Patient presents with uncontrolled diabetes and hypertension.
```

### Step 5. LangChain and OpenAI extract candidate conditions

The extractor in [backend/ai/prompts/extractor.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/prompts/extractor.py) sends the note plus the system prompt to the LLM.

The prompt asks the model to return JSON like this:

```json
{
  "conditions": [
    {
      "name": "condition name",
      "confidence": 0.0,
      "evidence": "short phrase from the note"
    }
  ]
}
```

A typical model response for this example would look like:

```json
{
  "conditions": [
    {
      "name": "uncontrolled diabetes",
      "confidence": 0.92,
      "evidence": "uncontrolled diabetes"
    },
    {
      "name": "hypertension",
      "confidence": 0.88,
      "evidence": "hypertension"
    }
  ]
}
```

Then the extractor normalizes the values:

- condition names are lowercased
- confidence values are converted to floats
- confidence is clamped into the `0.0` to `1.0` range
- empty or malformed condition names are skipped

Internal extracted result:

```text
[
  ExtractedCondition(name="uncontrolled diabetes", confidence=0.92, evidence="uncontrolled diabetes"),
  ExtractedCondition(name="hypertension", confidence=0.88, evidence="hypertension")
]
```

### Step 6. ICD mapper loads the curated dataset

The mapping layer in [backend/ai/mapping/icd_mapper.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/ai/mapping/icd_mapper.py) reads [backend/data/icd_codes.csv](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/data/icd_codes.csv).

Relevant CSV rows for this example:

```text
E11,Type 2 diabetes mellitus,diabetes mellitus,diabetes|type 2 diabetes|uncontrolled diabetes
I10,Essential hypertension,hypertension,hypertension|high blood pressure
```

### Step 7. Mapper matches extracted conditions to ICD rows

The mapper checks each extracted condition against:

- `canonical_name`
- `aliases`
- simple partial alias containment

For this example:

1. `uncontrolled diabetes`
   matches the alias `uncontrolled diabetes`
   so it maps to:

```json
{
  "code": "E11",
  "description": "Type 2 diabetes mellitus",
  "confidence": 0.92
}
```

2. `hypertension`
   matches the canonical name `hypertension`
   so it maps to:

```json
{
  "code": "I10",
  "description": "Essential hypertension",
  "confidence": 0.88
}
```

If the same ICD code were matched more than once, the mapper would keep only one copy.

### Step 8. Service builds the explanation

Back in [backend/app/services/prediction_service.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/services/prediction_service.py), the service sees that mapped codes were found and generates:

```text
Mapped extracted conditions to ICD-10 codes for: Type 2 diabetes mellitus, Essential hypertension.
```

### Step 9. API returns the final response

Final response returned by `POST /predict`:

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
  "explanation": "Mapped extracted conditions to ICD-10 codes for: Type 2 diabetes mellitus, Essential hypertension."
}
```

### Summary of the example flow

```text
Raw note
-> Request validation
-> PredictionService
-> LLM extracts "uncontrolled diabetes" and "hypertension"
-> ICD mapper matches E11 and I10 from CSV
-> Service builds explanation
-> API returns normalized JSON response
```

## Configuration

File: [backend/app/utils/config.py](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/app/utils/config.py)

Supported settings:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- dataset path for the curated ICD CSV

Environment file template:

File: [backend/.env.example](/abs/path/c:/Users/2000114884/Desktop/AI%20lab/AI-Medical-Coding-Assistant/backend/.env.example)

Suggested setup:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## How To Run

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Dependency note:

- `langchain-openai==0.2.6` requires `openai>=1.54.0`
- the requirements file is pinned accordingly to avoid resolver conflicts during install

Create environment file:

```bash
copy backend\\.env.example backend\\.env
```

Run the API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Frontend environment file:

```bash
copy frontend\\.env.example frontend\\.env
```

Default frontend API target:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## How To Test

Run test suite:

```bash
pytest
```

Current test coverage includes:

- successful `POST /predict` response
- successful `POST /predict-from-file` response
- validation failure for empty text
- validation failure for malformed payloads
- validation failure for missing uploaded files
- unsupported image type handling
- OCR failure handling without crashes
- graceful error handling when the service fails
- mapping known conditions to ICD codes
- deduplication of repeated conditions
- unknown-condition handling without crashes

## Current Limitations

- The dataset is intentionally small and not clinically complete
- Confidence values are accepted from the model and normalized, but not clinically calibrated
- The mapping logic is basic and may need stronger synonym handling later
- No authentication or persistence is included yet
- The implementation depends on a valid OpenAI API key for live extraction
- OCR support is image-only in the current implementation
- PDF upload is not included yet

## Recommended Next Steps

- Add mocked integration tests around LLM response parsing edge cases
- Expand the curated ICD dataset
- Add health and readiness endpoints
- Introduce structured logging and request tracing
- Add frontend integration once the Phase 1 API is stable
