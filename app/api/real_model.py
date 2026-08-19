# app/api/real_model.py — swappable model, SAME interface as mock_predict.
# This is why main.py only needs its import line changed to switch from mock to real.
from pathlib import Path
import joblib

from src.preprocessing import clean_text  # reuse the exact cleaning used at training time

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"

# Loaded once when this module is imported (i.e. once per API startup) —
# NOT inside real_predict(), which would reload the model from disk on every
# single request and make the API painfully slow.
_vectorizer = joblib.load(MODEL_DIR / "tfidf_vectorizer.joblib")
_model = joblib.load(MODEL_DIR / "fraud_classifier.joblib")
_coefs = _model.coef_[0]
_feature_names = _vectorizer.get_feature_names_out()

VERDICT_THRESHOLDS = {"high_risk": 0.6, "medium_risk": 0.3}  # kept identical to mock_model's


def _top_contributing_terms(text_vector, top_n: int = 3) -> list[dict]:
    """Explainability without SHAP: for THIS specific document, find which
    words/phrases pushed the prediction most toward 'fraudulent' by ranking
    (tfidf value in this doc) * (that term's learned coefficient).

    NOTE: unlike mock_model's fixed FLAG_POOL (e.g. "no_company_logo"), these
    flags are raw terms the model actually learned from — e.g. "wire_transfer"
    or "processing_fee". That's a real trade-off: more honest/data-driven,
    but less polished for a UI. Worth curating a mapping from top terms to
    friendlier labels once you see what the model actually surfaces.
    """
    indices = text_vector.nonzero()[1]
    contributions = [(i, text_vector[0, i] * _coefs[i]) for i in indices]
    contributions.sort(key=lambda pair: pair[1], reverse=True)

    flags = []
    for idx, contribution in contributions[:top_n]:
        if contribution <= 0:
            continue
        term = _feature_names[idx]
        flags.append({
            "flag": term.replace(" ", "_"),
            "evidence": f"Term '{term}' strongly associated with fraudulent postings in training data",
        })
    return flags


def real_predict(posting_text: str) -> dict:
    text = clean_text(posting_text)
    vec = _vectorizer.transform([text])

    proba_fraud = _model.predict_proba(vec)[0][1]
    score = round(float(proba_fraud), 2)

    if score > VERDICT_THRESHOLDS["high_risk"]:
        verdict = "high_risk"
    elif score > VERDICT_THRESHOLDS["medium_risk"]:
        verdict = "medium_risk"
    else:
        verdict = "low_risk"

    red_flags = _top_contributing_terms(vec) if score > VERDICT_THRESHOLDS["medium_risk"] else []
    confidence = round(float(max(proba_fraud, 1 - proba_fraud)), 2)

    return {
        "risk_score": score,
        "verdict": verdict,
        "red_flags": red_flags,
        "confidence": confidence,
    }
