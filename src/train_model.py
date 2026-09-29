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


if __name__ == "__main__":
    main()