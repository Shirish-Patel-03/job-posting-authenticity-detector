# src/train_model.py — trains the baseline fraud classifier and saves it for the API to load.
# Run this from inside src/:   python train_model.py
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from src.preprocessing import load_and_clean, combine_text_fields

DATA_PATH = "../data/emscad_core.csv"
MODEL_DIR = Path("../models")


def main():
    MODEL_DIR.mkdir(exist_ok=True)

    df = load_and_clean(DATA_PATH)
    df = combine_text_fields(df)

    X = df["full_text"]
    y = df["fraudulent"]

    # stratify=y matters here — fraud is ~4.27% of postings, so a plain random
    # split can easily starve the test set of fraud examples entirely
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),   # unigrams + bigrams — catches phrases like "wire transfer"
        stop_words="english",
        min_df=2,              # drop words that appear in only one posting (noise)
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # class_weight="balanced" matters here — without it, the model can hit
    # ~96% accuracy by predicting "not fraud" every single time, since fraud
    # is rare. Balanced weighting forces it to actually learn the minority class.
    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train_vec, y_train)

    y_pred = model.predict(X_test_vec)
    # Report precision/recall/F1 for the "fraudulent" class specifically —
    # accuracy alone will look great here and tell you almost nothing.
    print(classification_report(y_test, y_pred, target_names=["genuine", "fraudulent"]))

    joblib.dump(vectorizer, MODEL_DIR / "tfidf_vectorizer.joblib")
    joblib.dump(model, MODEL_DIR / "fraud_classifier.joblib")
    print(f"Saved model + vectorizer to {MODEL_DIR}/")


if __name__ == "__main__":
    main()
