import datetime

from sqlalchemy.orm import Session

from app.models import UnderwritingRecord, Policy, PaymentRecord


class PolicyError(Exception):
    def __init__(self, message: str):
        self.message = message


def _generate_policy_no() -> str:
    now = datetime.datetime.now()
    date_part = now.strftime("%Y%m%d")
    seq = now.microsecond % 1000000
    return f"P{date_part}{seq:06d}"


def issue_policy(db: Session, underwriting_id: int) -> Policy:
    record = (
        db.query(UnderwritingRecord)
        .filter(UnderwritingRecord.id == underwriting_id)
        .first()
    )
    if not record:
        raise PolicyError("核保记录不存在")
    if record.status != "approved":
        raise PolicyError(f"核保状态为 {record.status}，无法出单")

    paid = (
        db.query(PaymentRecord)
        .filter(
            PaymentRecord.underwriting_id == underwriting_id,
            PaymentRecord.status == "success",
        )
        .first()
    )
    if not paid:
        raise PolicyError("核保单尚未支付，无法出单")

    existing = db.query(Policy).filter(Policy.underwriting_id == underwriting_id).first()
    if existing:
        raise PolicyError("该核保记录已出单")

    today = datetime.date.today()
    policy = Policy(
        policy_no=_generate_policy_no(),
        underwriting_id=underwriting_id,
        product_id=record.product_id,
        effective_date=today,
        expiry_date=datetime.date(today.year + 1, today.month, today.day),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy
