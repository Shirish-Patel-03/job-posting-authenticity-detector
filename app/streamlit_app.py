# app/streamlit_app.py — temporary demo UI for showing the working pipeline.
# Calls the real /analyze endpoint (make sure the FastAPI server is running first).

import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/analyze"

st.set_page_config(page_title="Job Posting Authenticity Detector", page_icon="🔍")

st.title("🔍 Job Posting Authenticity Detector")
st.write(
    "Paste a job posting below and this tool will estimate how likely it is "
    "to be fraudulent, along with the specific terms driving that assessment."
)

posting_text = st.text_area(
    "Job posting text",
    height=250,
    placeholder="Paste the full job description here (at least 30 characters)...",
)

if st.button("Analyze Posting", type="primary"):
    if not posting_text.strip():
        st.warning("Please paste a job posting first.")
    else:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(API_URL, json={"posting_text": posting_text})
            except requests.exceptions.ConnectionError:
                st.error(
                    "Could not connect to the API. Make sure the FastAPI server "
                    "is running: `python -m uvicorn app.api.main:app --reload`"
                )
                st.stop()

        if response.status_code == 422:
            st.warning(response.json()["detail"][0]["msg"])
        elif response.status_code != 200:
            st.error(f"Unexpected error (status {response.status_code}): {response.text}")
        else:
            result = response.json()

            verdict = result["verdict"]
            verdict_display = {
                "high_risk": ("🔴 High Risk", "red"),
                "medium_risk": ("🟡 Medium Risk", "orange"),
                "low_risk": ("🟢 Low Risk", "green"),
            }
            label, color = verdict_display[verdict]

            st.subheader(label)

            col1, col2 = st.columns(2)
            col1.metric("Risk Score", f"{result['risk_score'] * 100:.0f}%")
            col2.metric("Model Confidence", f"{result['confidence'] * 100:.0f}%")

            st.progress(result["risk_score"])

            if result["red_flags"]:
                st.markdown("### Why this score?")
                for flag in result["red_flags"]:
                    st.markdown(f"- **{flag['flag']}** — {flag['evidence']}")
            else:
                st.markdown("### No specific red flags detected")

            with st.expander("Raw API response"):
                st.json(result)

st.divider()
st.caption(
    "This is an early-stage demo. The current model is text-only; structured "
    "signals (e.g. company logo presence) are planned for a future version."
)