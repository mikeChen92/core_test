from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UnderwritingRecord
from app.schemas import UnderwritingCreate, UnderwritingResponse, ErrorDetail
from app.services.underwriting import assess_risk, UnderwritingError

router = APIRouter(prefix="/api/underwriting", tags=["underwriting"])


@router.post("", response_model=UnderwritingResponse, status_code=201)
def create_underwriting(data: UnderwritingCreate, db: Session = Depends(get_db)):
    try:
        record = assess_risk(db, data)
    except UnderwritingError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "UNDERWRITING_REJECTED", "message": e.message},
        )
    return record


@router.get("/{underwriting_id}", response_model=UnderwritingResponse)
def get_underwriting(underwriting_id: int, db: Session = Depends(get_db)):
    record = (
        db.query(UnderwritingRecord)
        .filter(UnderwritingRecord.id == underwriting_id)
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": "RECORD_NOT_FOUND", "message": "核保记录不存在"},
        )
    return record
