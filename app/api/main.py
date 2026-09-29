import uuid
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.schemas import AnalyzeRequest, AnalyzeResponse
from app.api.real_model import real_predict
from app.api.llm_explainer import narrate_red_flags, assess_plausibility
from app.api.verification import build_verification_links
from app.api.pdf_report import generate_report_pdf
from app.db.database import engine, Base, get_db
from app.db.models import PredictionLog

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    result = real_predict(request.posting_text)

    plausibility = assess_plausibility(request.posting_text)
    if plausibility["implausible"] and result["risk_score"] < 0.6:
        result["risk_score"] = max(result["risk_score"], 0.65)
        result["verdict"] = "high_risk"
        result["red_flags"].append({"flag": "implausible_content", "evidence": plausibility["reason"]})

    explanation = narrate_red_flags(result["risk_score"], result["verdict"], result["red_flags"])
    links = build_verification_links(request.company_name)

    log = PredictionLog(
        check_id=str(uuid.uuid4()),
        posting_text=request.posting_text,
        risk_score=result["risk_score"],
        verdict=result["verdict"],
        confidence=result["confidence"],
        red_flags=result["red_flags"],
        source="text",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        **result,
        "check_id": log.check_id,
        "created_at": log.created_at.isoformat(),
        "explanation": explanation,
        "verification_links": links,
    }


@app.get("/report/{check_id}")
def download_report(check_id: str, db: Session = Depends(get_db)):
    log = db.query(PredictionLog).filter(PredictionLog.check_id == check_id).first()
    if not log:
        return {"error": "check_id not found"}
    explanation = narrate_red_flags(log.risk_score, log.verdict, log.red_flags)
    filepath = generate_report_pdf(
        check_id, log.posting_text, log.risk_score, log.verdict,
        log.red_flags, explanation, log.created_at.isoformat(),
    )
    return FileResponse(filepath, media_type="application/pdf", filename=f"report_{check_id}.pdf")


@app.get("/history")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    logs = (
        db.query(PredictionLog)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs