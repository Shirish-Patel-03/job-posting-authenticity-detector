from pydantic import BaseModel, field_validator
from typing import Literal


class RedFlag(BaseModel):
    flag: str
    evidence: str


class AnalyzeRequest(BaseModel):
    posting_text: str

    @field_validator("posting_text")
    @classmethod
    def must_look_like_a_description(cls, v: str) -> str:
        stripped = v.strip()
        # 30 chars is deliberately low — just enough to reject empty strings,
        # whitespace, and bare titles like "Software Engineer" without being
        # so strict it rejects genuinely short real postings
        if len(stripped) < 30:
            raise ValueError(
                "posting_text must be at least 30 characters — paste the full "
                "job description, not just a title"
            )
        return stripped


class AnalyzeResponse(BaseModel):
    # matches CONTRACTS.md Contract 2 exactly: Contract 1's 4 fields, plus
    # check_id + created_at for the dashboard history feature
    risk_score: float
    verdict: Literal["low_risk", "medium_risk", "high_risk"]
    red_flags: list[RedFlag]
    confidence: float
    check_id: str
    created_at: str
