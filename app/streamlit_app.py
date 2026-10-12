import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"
ANALYZE_URL = f"{API_BASE}/analyze"

st.set_page_config(
    page_title="Job Posting Authenticity Detector",
    page_icon="🔍",
    layout="centered",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background-color: #0F1115;
}

/* ---- Cover ---- */
.case-title {
    font-family: 'Source Serif 4', serif;
    font-weight: 700;
    font-size: 2.1rem;
    color: #E8E6E0;
    margin-bottom: 0.1rem;
    letter-spacing: -0.01em;
}
.case-subtitle {
    color: #8B8F99;
    font-size: 0.95rem;
    max-width: 480px;
    line-height: 1.5;
    margin-bottom: 1rem;
}
.case-rule {
    border: none;
    border-top: 1px solid #2A2E38;
    margin: 1.2rem 0 1.6rem 0;
}
.dataset-line {
    color: #6B6F79;
    font-size: 0.82rem;
    margin-bottom: 1.8rem;
}
.dataset-line b { color: #C9A227; font-weight: 600; }

/* ---- Inputs ---- */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #171A21 !important;
    border: 1px solid #2A2E38 !important;
    border-radius: 4px !important;
    color: #E8E6E0 !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #C9A227 !important;
    box-shadow: none !important;
}
label, .stMarkdown p { color: #B8BBC3 !important; }

[data-testid="stExpander"] {
    background-color: #12151C;
    border: 1px solid #2A2E38;
    border-radius: 4px;
}

.stButton button {
    background-color: #C9A227 !important;
    color: #0F1115 !important;
    border: none !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
}
.stButton button:hover {
    background-color: #DDB643 !important;
}

/* ---- Verdict stamp ---- */
.stamp-wrap {
    display: flex;
    justify-content: center;
    margin: 1.8rem 0 1.4rem 0;
}
.stamp {
    font-family: 'Source Serif 4', serif;
    font-weight: 700;
    font-size: 1.3rem;
    letter-spacing: 0.06em;
    padding: 0.7rem 1.8rem;
    border: 3px double currentColor;
    border-radius: 6px;
    transform: rotate(-2.5deg);
    text-transform: uppercase;
}
.stamp-high { color: #D64545; }
.stamp-medium { color: #CB9C3C; }
.stamp-low { color: #4F9D69; }

/* ---- Score block ---- */
.score-row {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-bottom: 1.4rem;
}
.score-item { text-align: center; }
.score-number {
    font-family: 'Source Serif 4', serif;
    font-size: 2.3rem;
    font-weight: 700;
    color: #E8E6E0;
    line-height: 1;
}
.score-label {
    color: #6B6F79;
    font-size: 0.78rem;
    margin-top: 0.3rem;
}

/* ---- Section labels ---- */
.doc-section {
    color: #C9A227;
    font-family: 'Source Serif 4', serif;
    font-size: 1rem;
    font-weight: 600;
    margin: 1.6rem 0 0.6rem 0;
    padding-bottom: 0.3rem;
    border-bottom: 1px solid #2A2E38;
}

/* ---- Case notes (flags) ---- */
.note-card {
    background-color: #12151C;
    border: 1px solid #2A2E38;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.6rem;
    position: relative;
}
.note-tag {
    position: absolute;
    top: -9px;
    right: 10px;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 3px;
    letter-spacing: 0.03em;
}
.note-tag.ml { background: #1E3A5F; color: #7FB0E0; }
.note-tag.llm { background: #3A1E5F; color: #B08FE0; }
.note-name {
    color: #E8E6E0;
    font-weight: 600;
    font-size: 0.92rem;
    margin-bottom: 0.2rem;
}
.note-evidence {
    color: #9A9DA6;
    font-size: 0.85rem;
    line-height: 1.5;
}

.stApp {
    background-color: #0F1115;
    background-image:
        radial-gradient(circle at 50% -10%, rgba(201,162,39,0.06), transparent 45%),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 28px);
}

.hero-wrap {
    position: relative;
    display: flex;
    justify-content: center;
    margin: 0.5rem 0 1.2rem 0;
    overflow: hidden;
    border-radius: 6px;
}
.hero-wrap::after {
    content: "";
    position: absolute;
    top: -20%;
    left: 0;
    width: 100%;
    height: 40%;
    background: linear-gradient(180deg, transparent, rgba(201,162,39,0.18), transparent);
    animation: scan 5s ease-in-out infinite;
}
@keyframes scan {
    0%   { transform: translateY(0%); }
    50%  { transform: translateY(260%); }
    100% { transform: translateY(0%); }
}

@keyframes stampIn {
    0%   { opacity: 0; transform: rotate(-2.5deg) scale(1.5); }
    100% { opacity: 1; transform: rotate(-2.5deg) scale(1); }
}
.stamp { animation: stampIn 0.45s ease-out; }


</style>
""", unsafe_allow_html=True)

# ---------- Cover ----------
st.markdown('<div class="case-title">🔍 Job Posting Authenticity Detector</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="case-subtitle">Paste a job posting below. It will be weighed against a '
    'trained fraud model and reviewed for logical plausibility, with the reasoning shown in full.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="dataset-line">Trained on <b>14,802</b> verified postings (EMSCAD) '
    '+ an LLM reasoning layer for contextual review</div>',
    unsafe_allow_html=True,
)
st.markdown('<hr class="case-rule">', unsafe_allow_html=True)

# ---------- Input ----------
company_name = st.text_input("Company name", placeholder="optional — enables verification links")

posting_text = st.text_area(
    "Job posting text",
    height=220,
    placeholder="Paste the full job description here (at least 30 characters)...",
)

if len(posting_text.strip()) > 0 and len(posting_text.split()) < 30:
    st.caption("⚠ Short text detected — accuracy improves with a full job description.")

with st.expander("Additional details (optional, improves accuracy)"):
    col1, col2 = st.columns(2)
    with col1:
        has_logo = st.selectbox("Company logo present?", ["unknown", "yes", "no"])
        has_questions = st.selectbox("Screening questions included?", ["unknown", "yes", "no"])
        salary_listed = st.selectbox("Salary range listed?", ["unknown", "yes", "no"])
    with col2:
        employment_type = st.selectbox(
            "Employment type",
            ["unknown", "full_time", "part_time", "contract", "temporary", "other"],
        )
        required_education = st.selectbox(
            "Required education",
            ["unknown", "high_school", "bachelors", "masters", "certification", "other"],
        )
        required_experience = st.selectbox(
            "Required experience",
            ["unknown", "internship", "entry", "associate", "mid_senior", "director_executive", "not_applicable"],
        )

analyze_clicked = st.button("Analyze Posting", type="primary", use_container_width=True)

# ---------- Results ----------
if analyze_clicked:
    if not posting_text.strip():
        st.warning("Please paste a job posting first.")
    else:
        payload = {
            "posting_text": posting_text,
            "company_name": company_name,
            "has_company_logo": has_logo,
            "has_screening_questions": has_questions,
            "salary_listed": salary_listed,
            "employment_type": employment_type,
            "required_education": required_education,
            "required_experience": required_experience,
        }
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(ANALYZE_URL, json=payload)
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the API. Make sure the FastAPI server is running: "
                    "`python -m uvicorn app.api.main:app --reload`"
                )
                st.stop()

        if response.status_code == 422:
            st.warning(response.json()["detail"][0]["msg"])
        elif response.status_code != 200:
            st.error(f"Unexpected error (status {response.status_code}): {response.text}")
        else:
            result = response.json()
            verdict = result["verdict"]

            stamp_meta = {
                "high_risk": ("Flagged — High Risk", "stamp-high"),
                "medium_risk": ("Flagged — Caution", "stamp-medium"),
                "low_risk": ("Appears Genuine", "stamp-low"),
            }
            stamp_text, stamp_class = stamp_meta[verdict]
            st.markdown(
                f'<div class="stamp-wrap"><div class="stamp {stamp_class}">{stamp_text}</div></div>',
                unsafe_allow_html=True,
            )

            st.markdown(
                f'<div class="score-row">'
                f'<div class="score-item"><div class="score-number">{result["risk_score"]*100:.0f}%</div>'
                f'<div class="score-label">RISK SCORE</div></div>'
                f'<div class="score-item"><div class="score-number">{result["confidence"]*100:.0f}%</div>'
                f'<div class="score-label">MODEL CONFIDENCE</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.progress(result["risk_score"])

            if result["confidence"] < 0.6:
                st.info("⚖ This posting has mixed signals — review the details yourself before deciding.")

            ml_flags = [f for f in result["red_flags"] if f.get("source", "ml_model") == "ml_model"]
            llm_flags = [f for f in result["red_flags"] if f.get("source") == "llm_reasoning"]

            if ml_flags:
                st.markdown('<div class="doc-section">Model Findings</div>', unsafe_allow_html=True)
                for flag in ml_flags:
                    st.markdown(
                        f'<div class="note-card"><span class="note-tag ml">ML</span>'
                        f'<div class="note-name">{flag["flag"]}</div>'
                        f'<div class="note-evidence">{flag["evidence"]}</div></div>',
                        unsafe_allow_html=True,
                    )

            if llm_flags:
                st.markdown('<div class="doc-section">Reasoning Notes</div>', unsafe_allow_html=True)
                for flag in llm_flags:
                    st.markdown(
                        f'<div class="note-card"><span class="note-tag llm">AI</span>'
                        f'<div class="note-name">{flag["flag"]}</div>'
                        f'<div class="note-evidence">{flag["evidence"]}</div></div>',
                        unsafe_allow_html=True,
                    )

            if not ml_flags and not llm_flags:
                st.markdown('<div class="doc-section">No specific findings</div>', unsafe_allow_html=True)

            st.markdown('<div class="doc-section">Summary</div>', unsafe_allow_html=True)
            st.write(result.get("explanation", ""))

            links = result.get("verification_links", {})
            if links:
                st.markdown('<div class="doc-section">Verify This Company</div>', unsafe_allow_html=True)
                cols = st.columns(len(links))
                for col, (name, url) in zip(cols, links.items()):
                    col.link_button(name.replace("_", " ").title(), url, use_container_width=True)

            st.markdown('<div class="doc-section">Report</div>', unsafe_allow_html=True)
            report_url = f"{API_BASE}/report/{result['check_id']}"
            st.link_button("Download PDF Report", report_url, use_container_width=True)

            with st.expander("Raw API response"):
                st.json(result)
st.markdown("""
<div class="hero-wrap">
<svg width="100%" height="160" viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="220" y="15" width="200" height="130" rx="3" fill="#171A21" stroke="#2A2E38" stroke-width="1.5"/>
  <line x1="245" y1="45" x2="395" y2="45" stroke="#3A3E48" stroke-width="2"/>
  <line x1="245" y1="62" x2="395" y2="62" stroke="#3A3E48" stroke-width="2"/>
  <line x1="245" y1="79" x2="360" y2="79" stroke="#3A3E48" stroke-width="2"/>
  <line x1="245" y1="96" x2="395" y2="96" stroke="#2A2E38" stroke-width="2"/>
  <line x1="245" y1="113" x2="330" y2="113" stroke="#2A2E38" stroke-width="2"/>
  <g transform="translate(255,100) rotate(-8)">
    <circle cx="0" cy="0" r="26" fill="none" stroke="#C9A227" stroke-width="3"/>
    <circle cx="0" cy="0" r="26" fill="#C9A227" fill-opacity="0.08"/>
    <text x="0" y="7" text-anchor="middle" font-family="Source Serif 4, serif" font-weight="700" font-size="13" fill="#C9A227">OK</text>
  </g>
  <g transform="translate(460,75) rotate(18)">
    <circle cx="0" cy="0" r="38" fill="none" stroke="#5B606C" stroke-width="5"/>
    <line x1="27" y1="27" x2="58" y2="58" stroke="#5B606C" stroke-width="7" stroke-linecap="round"/>
  </g>
</svg>
</div>
""", unsafe_allow_html=True)
st.markdown('<hr class="case-rule">', unsafe_allow_html=True)
st.caption(
    "Early-stage demo. The model combines statistical text analysis with structured posting "
    "signals and an LLM reasoning layer. Known limitation: the training dataset is from "
    "2012–2014, so very recent scam vocabulary may be under-detected by the statistical layer alone."
)