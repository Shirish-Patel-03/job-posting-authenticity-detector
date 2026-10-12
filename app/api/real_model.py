from pathlib import Path
import joblib
from src.preprocessing import clean_text

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"

_pipeline = joblib.load(MODEL_DIR / "fraud_pipeline.joblib")
_term_stats = joblib.load(MODEL_DIR / "term_stats.joblib")
_dataset_info = joblib.load(MODEL_DIR / "dataset_info.joblib")

_text_transformer = _pipeline.named_steps["features"].named_transformers_["text"]
_feature_names = _text_transformer.get_feature_names_out()
_coefs = _pipeline.named_steps["clf"].coef_[0][: len(_feature_names)]

VERDICT_THRESHOLDS = {"high_risk": 0.6, "medium_risk": 0.3}


def _top_contributing_terms(text: str, top_n: int = 3) -> list[dict]:
    """Explainability grounded in real training-data statistics, not just a
    vague coefficient ranking — each flag cites actual fraud rates from the
    EMSCAD training set."""
    text_vec = _text_transformer.transform([text])
    indices = text_vec.nonzero()[1]
    contributions = [(i, text_vec[0, i] * _coefs[i]) for i in indices]
    contributions.sort(key=lambda pair: pair[1], reverse=True)

    flags = []
    for idx, contribution in contributions:
        if contribution <= 0 or len(flags) >= top_n:
            break
        term = _feature_names[idx]
        stat = _term_stats.get(term)
        if stat:
            evidence = (
                f"Postings containing '{term}' were fraudulent {stat['rate_with']:.0%} of "
                f"the time in our {_dataset_info['total_postings']:,}-posting training set "
                f"(vs {stat['rate_without']:.0%} baseline), based on {stat['count']} occurrences."
            )
        else:
            evidence = f"Term '{term}' contributed to this prediction based on patterns learned from training data."
        flags.append({"flag": term.replace(" ", "_"), "evidence": evidence, "source": "ml_model"})
    return flags


def real_predict(posting_text: str, **structured_fields) -> dict:
    from src.preprocessing import build_request_features
    text = clean_text(posting_text)
    row = build_request_features(posting_text, **structured_fields)

    proba_fraud = _pipeline.predict_proba(row)[0][1]
    score = round(float(proba_fraud), 2)

    if score > VERDICT_THRESHOLDS["high_risk"]:
        verdict = "high_risk"
    elif score > VERDICT_THRESHOLDS["medium_risk"]:
        verdict = "medium_risk"
    else:
        verdict = "low_risk"

    red_flags = _top_contributing_terms(text) if score > VERDICT_THRESHOLDS["medium_risk"] else []
    confidence = round(float(max(proba_fraud, 1 - proba_fraud)), 2)

    return {
        "risk_score": score,
        "verdict": verdict,
        "red_flags": red_flags,
        "confidence": confidence,
        "dataset_info": _dataset_info,
    }