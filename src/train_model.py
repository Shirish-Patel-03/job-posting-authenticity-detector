import joblib
from pathlib import Path
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

from preprocessing import (
    load_and_clean, combine_text_fields, build_training_features,
    STRUCTURED_COLUMNS, NUMERIC_SIGNAL_COLUMNS, BINARY_SIGNAL_COLUMNS,
)

DATA_PATH = "../data/emscad_core.csv"
MODEL_DIR = Path("../models")


def compute_term_stats(full_text_series, y, top_terms, min_occurrences=5):
    """For each of the model's top learned terms, compute the REAL fraud rate
    among training postings that contain it vs. don't — gives the explainer
    actual dataset-backed numbers to cite instead of a vague claim."""
    stats = {}
    contains = full_text_series.str.contains
    for term in top_terms:
        pattern = re.escape(term.replace("_", " "))
        mask = contains(pattern, case=False, regex=True, na=False)
        count_with = mask.sum()
        if count_with < min_occurrences:
            continue
        rate_with = y[mask].mean()
        rate_without = y[~mask].mean()
        stats[term] = {
            "rate_with": round(float(rate_with), 3),
            "rate_without": round(float(rate_without), 3),
            "count": int(count_with),
        }
    return stats


import re  # noqa: E402 (kept near usage above for clarity)


def main():
    MODEL_DIR.mkdir(exist_ok=True)

    df = load_and_clean(DATA_PATH)
    df = combine_text_fields(df)
    X = build_training_features(df)
    y = df["fraudulent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(transformers=[
        ("text", TfidfVectorizer(max_features=20000, ngram_range=(1, 2), stop_words="english", min_df=2), "full_text"),
        ("cat", OneHotEncoder(handle_unknown="ignore"), STRUCTURED_COLUMNS),
        ("num", "passthrough", NUMERIC_SIGNAL_COLUMNS + BINARY_SIGNAL_COLUMNS),
    ])

    pipeline = Pipeline([
        ("features", preprocessor),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000)),
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    print(classification_report(y_test, y_pred, target_names=["genuine", "fraudulent"]))
    print("Confusion matrix (rows=actual, cols=predicted):")
    print(confusion_matrix(y_test, y_pred))

    joblib.dump(pipeline, MODEL_DIR / "fraud_pipeline.joblib")
    print(f"Saved combined pipeline to {MODEL_DIR}/fraud_pipeline.joblib")

    # --- Term statistics for explainability ---
    text_transformer = pipeline.named_steps["features"].named_transformers_["text"]
    feature_names = text_transformer.get_feature_names_out()
    coefs = pipeline.named_steps["clf"].coef_[0][: len(feature_names)]
    top_indices = coefs.argsort()[::-1][:150]  # top 150 candidate terms
    top_terms = [feature_names[i] for i in top_indices]

    stats = compute_term_stats(X["full_text"], y, top_terms)
    joblib.dump(stats, MODEL_DIR / "term_stats.joblib")
    print(f"Saved statistics for {len(stats)} terms to {MODEL_DIR}/term_stats.joblib")

    dataset_info = {
        "total_postings": len(df),
        "fraud_rate": round(float(y.mean()), 4),
        "fraud_count": int(y.sum()),
    }
    joblib.dump(dataset_info, MODEL_DIR / "dataset_info.joblib")
    print(f"Dataset info: {dataset_info}")


if __name__ == "__main__":
    main()