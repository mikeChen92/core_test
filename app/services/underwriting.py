from sqlalchemy.orm import Session

from app.models import UnderwritingRecord, Product
from app.schemas import UnderwritingCreate


class UnderwritingError(Exception):
    def __init__(self, message: str):
        self.message = message


def assess_risk(db: Session, data: UnderwritingCreate) -> UnderwritingRecord:
    """Evaluate underwriting application with simple rules."""
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise UnderwritingError("产品不存在")

    if data.insured_age < 18 or data.insured_age > 65:
        raise UnderwritingError(f"被保人年龄 {data.insured_age} 不在承保范围（18-65周岁）")

    existing_rejected = (
        db.query(UnderwritingRecord)
        .filter(
            UnderwritingRecord.insured_id_no == data.insured_id_no,
            UnderwritingRecord.status == "rejected",
        )
        .first()
    )
    if existing_rejected:
        raise UnderwritingError(f"被保人 {data.insured_name} 存在未结清的拒保记录")

    record = UnderwritingRecord(
        product_id=data.product_id,
        applicant_name=data.applicant_name,
        applicant_id_no=data.applicant_id_no,
        insured_name=data.insured_name,
        insured_id_no=data.insured_id_no,
        insured_age=data.insured_age,
        status="approved",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
