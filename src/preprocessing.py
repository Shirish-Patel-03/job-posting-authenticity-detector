# src/preprocessing.py — Week 1 EDA decisions + Week 2 feature engineering for the baseline model
import re
import pandas as pd

TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]


def load_and_clean(filepath: str) -> pd.DataFrame:
    """Load EMSCAD, apply all cleaning decisions from Week 1 EDA."""
    df = pd.read_csv(filepath, encoding="latin1")
    # Step 1: deduplicate by description (same posting scraped multiple times)
    df = df.drop_duplicates(subset="description", keep="first")
    # Step 2: create the salary_missing flag
    df["salary_missing"] = df["salary_range"].isnull()
    return df


def clean_salary(df: pd.DataFrame) -> pd.DataFrame:
    """Apply salary_range cleaning decisions: remove Excel-corrupted dates,
    exclude likely non-annual (hourly/weekly) values, exclude extreme outliers."""

    df["salary_lower_bound"] = float("nan")
    # Only attempt to parse rows where salary_range is actually present
    has_salary = ~df["salary_missing"]
    # Step 1: exclude Excel date-corrupted values (contain letters, e.g. "Oct-15")
    is_corrupted = df["salary_range"].str.contains("[A-Za-z]", na=False)
    parseable = has_salary & ~is_corrupted
    # Step 2: parse the lower bound from valid "X-Y" strings
    lower = df.loc[parseable, "salary_range"].str.split("-").str[0].astype(float)
    # Step 3: exclude likely non-annual (under 1000) and extreme outliers (over 1,000,000)
    is_realistic = (lower >= 1000) & (lower <= 1000000)
    df.loc[lower[is_realistic].index, "salary_lower_bound"] = lower[is_realistic]
    return df


def clean_text(text: str) -> str:
    """Strip HTML tags/entities and normalize whitespace. EMSCAD's text fields
    are scraped straight off job boards and are full of raw HTML (<p>, &amp;, etc).
    This is called both at training time and at inference time — it MUST stay
    identical in both places or the model will see different-looking input
    than it was trained on."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML tags
    text = re.sub(r"&\w+;", " ", text)             # strip HTML entities (&amp; etc)
    text = re.sub(r"http\S+|www\.\S+", " ", text)  # strip URLs
    text = re.sub(r"\s+", " ", text).strip()       # collapse whitespace
    return text


def combine_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Build the single `full_text` column the model actually trains on.

    IMPORTANT DESIGN NOTE: PredictRequest (schemas.py) only sends
    `posting_text` — one string, no structured fields like has_company_logo
    or telecommuting. So a baseline model can only use TEXT-derived features,
    otherwise training and inference would see different feature sets.
    If you later want to use those structured EMSCAD columns as real signals,
    PredictRequest needs to be extended first to actually collect them from
    the user — that's a schema change, not just a model change.
    """
    for col in TEXT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").apply(clean_text)

    df["full_text"] = df[TEXT_COLUMNS].agg(" ".join, axis=1).str.strip()
    return df

# Structured Field addition/implementation
STRUCTURED_COLUMNS = [
    "has_company_logo", "has_screening_questions", "salary_listed",
    "employment_type", "required_education", "required_experience",
]

_EMPLOYMENT_MAP = {
    "Full-time": "full_time", "Part-time": "part_time", "Contract": "contract",
    "Temporary": "temporary", "Other": "other",
}
_EDUCATION_MAP = {
    "High School or equivalent": "high_school", "Bachelor's Degree": "bachelors",
    "Master's Degree": "masters", "Certification": "certification",
}
_EXPERIENCE_MAP = {
    "Internship": "internship", "Entry level": "entry", "Associate": "associate",
    "Mid-Senior level": "mid_senior", "Director": "director_executive",
    "Executive": "director_executive", "Not Applicable": "not_applicable",
}


def _map_with_fallback(series, mapping, fallback, unknown_values=()):
    """Blank or explicitly-unspecified -> 'unknown'; listed values -> API vocabulary;
    anything rare and unlisted -> fallback (e.g. 'other')."""
    def convert(v):
        if pd.isna(v) or v in unknown_values:
            return "unknown"
        return mapping.get(v, fallback)
    return series.apply(convert)


def build_training_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn the cleaned EMSCAD frame (after combine_text_fields) into the exact
    seven-column table the model trains on, in the API's vocabulary."""
    out = pd.DataFrame(index=df.index)
    out["full_text"] = df["full_text"]
    out["has_company_logo"] = df["has_company_logo"].map({1: "yes", 0: "no"})
    out["has_screening_questions"] = df["has_questions"].map({1: "yes", 0: "no"})
    out["salary_listed"] = df["salary_missing"].map({True: "no", False: "yes"})
    out["employment_type"] = _map_with_fallback(df["employment_type"], _EMPLOYMENT_MAP, "other")
    out["required_education"] = _map_with_fallback(
        df["required_education"], _EDUCATION_MAP, "other", unknown_values=("Unspecified",)
    )
    out["required_experience"] = _map_with_fallback(df["required_experience"], _EXPERIENCE_MAP, "unknown")
    out["full_text"] = df["full_text"]  # keep, already there — just confirming placement
    out = add_text_signal_features(out)
    return out


def build_request_features(posting_text: str, **structured) -> pd.DataFrame:
    """Same table, one row, from a live API request."""
    row = {col: structured.get(col, "unknown") for col in STRUCTURED_COLUMNS}
    row["full_text"] = clean_text(posting_text)
    df = pd.DataFrame([row])
    return add_text_signal_features(df)


def add_text_signal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cheap engineered features derived from full_text — targets vocabulary
    drift and scam-copy patterns not captured by TF-IDF word matching alone."""
    df = df.copy()
    df["has_currency"] = df["full_text"].str.contains(r"[$₹€£]", regex=True).astype(int)
    df["urgency_count"] = df["full_text"].str.count(
        r"\b(urgent|immediately|apply now|limited spots|act now|hurry)\b", flags=re.IGNORECASE
    )
    return df


NUMERIC_SIGNAL_COLUMNS = ["urgency_count"]
BINARY_SIGNAL_COLUMNS = ["has_currency"]

if __name__ == "__main__":
    df = load_and_clean("../data/emscad_core.csv")
    print(df.shape)
    print(df["fraudulent"].mean())
    df = clean_salary(df)
    print(df["salary_lower_bound"].describe())
    print(f"Usable salary values: {df['salary_lower_bound'].notna().sum()}")
    df = combine_text_fields(df)
    print(df[["full_text"]].head(2))
