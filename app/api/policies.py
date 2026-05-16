from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Policy
from app.schemas import PolicyCreate, PolicyResponse, PolicyListResponse, ErrorDetail
from app.services.policy import issue_policy, PolicyError

router = APIRouter(prefix="/api/policies", tags=["policies"])


@router.post("", response_model=PolicyResponse, status_code=201)
def create_policy(data: PolicyCreate, db: Session = Depends(get_db)):
    try:
        policy = issue_policy(db, data.underwriting_id)
    except PolicyError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "POLICY_ERROR", "message": e.message},
        )
    return policy


@router.get("", response_model=PolicyListResponse)
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(Policy).all()
    return {"policies": policies}


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=404,
            detail={"code": "POLICY_NOT_FOUND", "message": "保单不存在"},
        )
    return policy
