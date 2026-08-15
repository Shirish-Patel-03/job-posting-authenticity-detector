# app/api/mock_model.py — swappable later, isolated in its own file
import random

FLAG_POOL = [
    ("no_company_logo", "No company logo present in posting"),
    ("unrealistic_salary", "Salary significantly above market rate for role"),
    ("vague_description", "Job description lacks specific responsibilities"),
    ("urgent_language", "Posting uses high-pressure urgency language"),
]

def mock_predict(posting_text: str) -> dict:
    is_fraud = random.random() < 0.0427  # matches real EMSCAD fraud rate
    score = random.uniform(0.6, 0.95) if is_fraud else random.uniform(0.02, 0.35)
    flags = random.sample(FLAG_POOL, k=random.randint(1, 3)) if is_fraud else []
    return {
        "risk_score": round(score, 2),
        "verdict": "high_risk" if score > 0.6 else "medium_risk" if score > 0.3 else "low_risk",
        "red_flags": [{"flag": f, "evidence": e} for f, e in flags],
        "confidence": round(random.uniform(0.7, 0.95), 2),
    }