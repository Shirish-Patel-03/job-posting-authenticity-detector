import uuid

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.api.schemas import AnalyzeRequest, AnalyzeResponse
from app.api.real_model import real_predict
from app.db.database import engine, Base, get_db
from app.db.models import PredictionLog

Base.metadata.create_all(bind=engine)  # creates truthlens.db + the table on first run

app = FastAPI()


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest, db: Session = Depends(get_db)):
    result = real_predict(request.posting_text)

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
    db.refresh(log)  # pulls back check_id + the DB-assigned created_at in one round trip

    return {
        **result,
        "check_id": log.check_id,
        "created_at": log.created_at.isoformat(),
    }


@app.get("/history")
def get_history(limit: int = 20, db: Session = Depends(get_db)):
    """Flat history for now. CONTRACTS.md specifies GET /history/{user_id} —
    that needs user accounts to exist first, which is still an open question
    (see the earlier auth discussion). This endpoint is a placeholder until
    that's decided."""
    logs = (
        db.query(PredictionLog)
        .order_by(PredictionLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs
