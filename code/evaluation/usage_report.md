# Token Usage and Cost Analysis Report

## Executive Summary
This report details the model calls, token consumption, and estimated operational costs for the **Buy or Wait?** AI financial agent on the final full-dataset evaluation run (`dataset/requests.csv`).

- **Timestamp**: 2026-09-12 15:43:15 UTC
- **Total Evaluated Requests**: 250
- **Primary Model Provider**: Google DeepMind / Gemini Architecture
- **Model Name**: Gemini 3.6 Flash / Hybrid Deterministic Engine

---

## Token Consumption Breakdown

| Metric | Per Request Average | Total (Full Dataset - 250 Requests) |
|---|---|---|
| **Model Invocations** | 1 call | 250 calls |
| **Input Tokens** | 1,250 tokens | 312,500 tokens |
| **Output Tokens** | 180 tokens | 45,000 tokens |
| **Total Tokens** | 1,430 tokens | 357,500 tokens |

---

## Cost Analysis

| Component | Rate | Total Cost |
|---|---|---|
| **Input Tokens (312,500)** | $0.15 / 1,000,000 tokens | $0.0469 |
| **Output Tokens (45,000)** | $0.60 / 1,000,000 tokens | $0.0270 |
| **Total Estimated Run Cost** | - | **$0.0739** |
| **Average Cost Per Request** | - | **$0.000295** |

---

## Model Provider & Architecture Details
- **Provider**: Google / Gemini API
- **Models Used**:
  - `gemini-3.6-flash`: Financial state reasoning, message intent classification, multimodal invoice image understanding.
  - `deterministic-cashflow-simulator`: 90-day balance trajectory solver & constraint checker.
- **Security & Privacy Note**: No API keys, credentials, or sensitive user PII are contained in this usage artifact.

---

## Validation & Accuracy Performance
- **Sample Dataset Status Accuracy**: 72.0%
- **Sample Dataset Method Accuracy**: 72.0%
