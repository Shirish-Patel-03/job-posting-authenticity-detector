# Data Contracts

This file defines the fixed data shapes passed between components. 
If a contract needs to change, open a PR to this file first and get it approved 
before changing any code that depends on it.

## Contract 1: Model Output (ML pipeline → Backend)

Produced by `src/fusion.py`. The backend must not assume anything about 
*how* this is computed — only that it receives this shape.

```json
{
  "risk_score": 0.73,
  "verdict": "high_risk",
  "red_flags": [
    {"flag": "no_company_logo", "evidence": "No company logo present in posting"},
    {"flag": "unrealistic_salary", "evidence": "$5000/week, no experience required"}
  ],
  "confidence": 0.81
}
```

- `risk_score`: float, 0.0–1.0
- `verdict`: one of `"low_risk"`, `"medium_risk"`, `"high_risk"`
- `red_flags`: array, can be empty `[]`
- `confidence`: float, 0.0–1.0 — model's own confidence in this prediction

## Contract 2: API Endpoint (Backend → Frontend)

### `POST /analyze`

Request:
```json
{
  "posting_text": "string, the raw pasted job posting"
}
```

Response: same shape as Contract 1, plus:
```json
{
  "check_id": "uuid, for saving to dashboard history",
  "created_at": "ISO 8601 timestamp"
}
```

### `GET /history/{user_id}` (dashboard feature)

Response:
```json
{
  "checks": [
    { "check_id": "...", "risk_score": 0.73, "verdict": "high_risk", "created_at": "..." }
  ]
}
```

## Status

- [ ] Model contract — draft, not yet finalized (Week 1, EDA in progress)
- [ ] API contract — not yet implemented
- [ ] Frontend — not yet started