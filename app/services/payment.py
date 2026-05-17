import datetime
import logging
import httpx

from sqlalchemy.orm import Session

from app.models import UnderwritingRecord, PaymentRecord

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    def __init__(self, message: str):
        self.message = message


def _generate_order_no() -> str:
    now = datetime.datetime.now()
    return f"ORD{now.strftime('%Y%m%d%H%M%S')}{now.microsecond % 10000:04d}"


def create_payment_order(db: Session, underwriting_id: int, callback_url: str) -> PaymentRecord:
    record = db.query(UnderwritingRecord).filter(UnderwritingRecord.id == underwriting_id).first()
    if not record:
        raise PaymentError("核保单不存在")
    if record.status != "approved":
        raise PaymentError("核保单状态异常，无法支付")

    existing = (
        db.query(PaymentRecord)
        .filter(PaymentRecord.underwriting_id == underwriting_id, PaymentRecord.status == "pending")
        .first()
    )
    if existing:
        return existing

    order_no = _generate_order_no()
    pmt = PaymentRecord(
        underwriting_id=underwriting_id,
        order_no=order_no,
        amount=record.product.premium,
        callback_url=callback_url,
    )
    db.add(pmt)
    db.commit()
    db.refresh(pmt)
    return pmt


def complete_payment(db: Session, order_no: str) -> PaymentRecord:
    record = (
        db.query(PaymentRecord)
        .filter(PaymentRecord.order_no == order_no)
        .first()
    )
    if not record:
        raise PaymentError("支付订单不存在")
    if record.status != "pending":
        raise PaymentError(f"支付订单状态为 {record.status}，无法完成支付")

    record.status = "success"
    record.paid_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(record)

    return record


def send_payment_callback(record: PaymentRecord) -> None:
    """Send payment success notification (call via BackgroundTasks)."""
    try:
        payload = {
            "order_no": record.order_no,
            "underwriting_id": record.underwriting_id,
            "amount": str(record.amount),
            "status": "success",
            "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        }
        httpx.post(record.callback_url, json=payload, timeout=5.0)
    except Exception as e:
        logger.warning("Payment callback failed for %s: %s", record.order_no, e)
