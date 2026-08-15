import pandas as pd


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
    
    df["salary_lower_bound"] = float("nan")  # changed from pd.NA

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

if __name__ == "__main__":
    df = load_and_clean("../data/emscad_core.csv")
    print(df.shape)
    print(df["fraudulent"].mean())

    df = clean_salary(df)
    print(df["salary_lower_bound"].describe())
    print(f"Usable salary values: {df['salary_lower_bound'].notna().sum()}")