# 🧠 AI Medical Coding Assistant

An AI-powered system that converts clinical text into standardized medical codes (ICD-10), improving accuracy and reducing manual effort in healthcare coding workflows.

---

# 📌 Project Overview

This project automates the process of mapping clinical notes to diagnosis codes using NLP and LLMs.

The system is built in **two phases**:

* **Phase 1** → Text-based input (core AI logic)
* **Phase 2** → OCR-based input (real-world document processing)

---

# 🎯 Objectives

* Extract medical entities (diseases, conditions) from clinical text
* Map extracted entities to ICD-10 codes
* Provide confidence scores and explanations
* Enable human-in-the-loop corrections

---

# 🏗️ Tech Stack

## Backend

* Python (FastAPI)

## AI / NLP

* LangChain
* OpenAI (LLM for extraction + mapping)

## Data Processing

* Pandas
* Custom ICD-10 mapping dataset

## Phase 2 Addional Tools

* EasyOCR
* PDF processing libraries

---

# 📂 Project Structure

```
ai-medical-coding/
│
├── app/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── ai/
│   ├── prompts/
│   ├── chains/
│   └── mapping/
│
├── data/
│   └── icd_codes.csv
│
├── tests/
│
├── requirements.txt
└── README.md
```

---

# 🚀 Phase 1: Text-Based Medical Coding

## 📌 Description

This phase focuses on processing **raw clinical text input** and generating ICD-10 code predictions.

## 🔄 Workflow

```
Clinical Text Input
        ↓
Text Preprocessing
        ↓
LangChain Pipeline
        ↓
OpenAI LLM
        ↓
Entity Extraction
        ↓
ICD Code Mapping
        ↓
Response (Codes + Confidence + Explanation)
```

---

## 🧪 Sample Input

```
Patient presents with uncontrolled diabetes and hypertension.
```

## ✅ Sample Output

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
  "explanation": "Identified keywords 'diabetes' and 'hypertension' from clinical text."
}
```

---

## ⚙️ Key Components

### 1. Prompt Engineering

* Extract diseases from text
* Map diseases to ICD codes
* Generate structured JSON output

### 2. LangChain Pipeline

* Input → Prompt Template → LLM → Output Parser

### 3. Mapping Layer

* ICD-10 dataset lookup
* Hybrid approach:

  * LLM + rule-based mapping

---

## ▶️ Running Phase 1

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Set environment variables

```
OPENAI_API_KEY=your_api_key
```

### 3. Run server

```
uvicorn app.main:app --reload
```

### 4. API Endpoint

```
POST /predict
```

### Request Body

```json
{
  "text": "Patient has asthma and chronic cough"
}
```

---

# 🧠 Phase 2: OCR-Based Medical Coding

## 📌 Description

This phase extends the system to process **scanned documents and prescriptions** using OCR.

---

## 🔄 Workflow

```
PDF / Image Upload
        ↓
EasyOCR
        ↓
Extracted Text
        ↓
Phase 1 Pipeline
        ↓
ICD Code Output
```

---

## ⚙️ Additional Components

### 1. OCR Integration

* AWS Textract for text extraction
* Support for:

  * PDFs
  * Scanned prescriptions
  * Medical reports

### 2. File Handling

* Upload API
* Temporary storage (S3 or local)

---

## ▶️ New API Endpoint

```
POST /predict-from-file
```

### Request

* Multipart file upload (PDF/Image)

---

# 📊 Evaluation Metrics

* Precision / Recall for code prediction
* Accuracy of entity extraction
* Human validation feedback

---

# 🔒 Security Considerations

* API key protection
* Avoid storing sensitive patient data
* Mask PII in logs

---

# 🚀 Future Enhancements

* Fine-tuned medical NLP models
* Multi-language support
* Real-time coding suggestions
* Integration with EHR systems

---

# ⚠️ Disclaimer

This project is for educational purposes only and should not be used for real clinical or billing decisions.

---

# 👨‍💻 Author

Harshil Savaliya

---
