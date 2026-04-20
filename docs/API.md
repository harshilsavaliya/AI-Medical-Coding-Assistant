# API Reference

## Base Behavior

The backend exposes two endpoints:

- `POST /predict`
- `POST /predict-from-file`

Both endpoints return the same response shape so the frontend can render a shared results workflow.

## POST /predict

Submit clinical text directly as JSON.

### Request

```json
{
  "text": "Patient presents with uncontrolled diabetes and hypertension."
}
```

### Validation

- `text` is required
- whitespace is normalized before processing
- empty or all-whitespace text is rejected with HTTP `422`

### Successful response

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

### Mixed-result response example

```json
{
  "codes": [
    {
      "code": "I10",
      "description": "Essential hypertension",
      "confidence": 0.88
    }
  ],
  "explanation": "Mapped extracted conditions to ICD-10 codes for: Essential hypertension. Additional extracted conditions need manual review.",
  "review_status": "needs_review",
  "extracted_conditions": [
    {
      "name": "hypertension",
      "confidence": 0.88,
      "evidence": "hypertension",
      "mapped_code": "I10"
    },
    {
      "name": "fatigue",
      "confidence": 0.51,
      "evidence": "fatigue",
      "mapped_code": null
    }
  ],
  "unmatched_conditions": ["fatigue"]
}
```

## POST /predict-from-file

Submit a medical image as multipart form data.

### Request

- content type: `multipart/form-data`
- field name: `file`
- supported upload types:
  - `image/jpeg`
  - `image/jpg`
  - `image/png`

### Behavior

- validates the uploaded file
- extracts OCR text with EasyOCR
- sends OCR text into the same `PredictionService` used by `/predict`
- returns the same response schema as `/predict`

## Response Fields

### `codes`

List of deduplicated ICD code suggestions returned from the curated dataset.

Fields:

- `code`
- `description`
- `confidence`

### `explanation`

Short human-readable summary of the result. This changes based on whether codes were found and whether manual review is still needed.

### `review_status`

Possible values:

- `auto_suggested`
- `needs_review`

Current logic:

- `auto_suggested` when extracted conditions exist, at least one code maps, and no extracted conditions remain unmatched
- `needs_review` otherwise

### `extracted_conditions`

Condition-level review records sourced from the model output after normalization.

Fields:

- `name`
- `confidence`
- `evidence`
- `mapped_code`

### `unmatched_conditions`

Normalized extracted condition names that did not match the curated ICD dataset.

## Error Behavior

### `/predict`

- `422` for request validation errors
- `502` when the prediction service fails, including LLM communication or parsing errors

### `/predict-from-file`

- `400` for unsupported file types
- `422` for unreadable files or OCR extraction failures
- `503` when OCR dependencies are unavailable
- `502` for broader file prediction service failures
