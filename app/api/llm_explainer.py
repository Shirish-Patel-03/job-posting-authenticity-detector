from dotenv import load_dotenv
load_dotenv()

import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
_llm = genai.GenerativeModel("gemini-2.5-flash")


def narrate_red_flags(risk_score: float, verdict: str, red_flags: list[dict]) -> str:
    if not os.environ.get("GEMINI_API_KEY"):
        return "AI explanation unavailable (GEMINI_API_KEY not set)."
    if not red_flags:
        return "No significant red flags were detected in this posting."

    flags_text = "\n".join(f"- {f['flag']}: {f['evidence']}" for f in red_flags)
    prompt = f"""A fraud-detection model scored this job posting {risk_score:.0%} risk ({verdict}).
Flagged signals:
{flags_text}

Write a 2-3 sentence plain-English explanation for a job seeker, explaining why
this posting looks risky based on these signals. Be direct and practical, not alarmist."""

    try:
        response = _llm.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"AI explanation unavailable ({type(e).__name__})."


def assess_plausibility(posting_text: str) -> dict:
    if not os.environ.get("GEMINI_API_KEY"):
        return {"implausible": False, "reason": ""}
    prompt = f"""Read this job posting. Ignoring word-level scam language, judge only
whether the posting is internally LOGICALLY PLAUSIBLE as a real job (contradictory
requirements, impossible demands, absurd/joke content count as implausible).

Posting:
{posting_text}

Respond with exactly one line: PLAUSIBLE or IMPLAUSIBLE, then a colon, then a one-sentence reason."""
    try:
        response = _llm.generate_content(prompt)
        text = response.text.strip()
        implausible = text.upper().startswith("IMPLAUSIBLE")
        reason = text.split(":", 1)[-1].strip() if ":" in text else ""
        return {"implausible": implausible, "reason": reason}
    except Exception:
        return {"implausible": False, "reason": ""}