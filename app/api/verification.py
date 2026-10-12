from urllib.parse import quote


def build_verification_links(company_name: str | None) -> dict:
    if not company_name or not company_name.strip():
        return {}
    q = quote(company_name.strip())
    return {
        "google_search": f"https://www.google.com/search?q={q}+company+reviews",
        "linkedin_search": f"https://www.linkedin.com/search/results/companies/?keywords={q}",
        "glassdoor_search": f"https://www.glassdoor.com/Search/results.htm?keyword={q}",
    }