import datetime
import httpx

from sqlalchemy.orm import Session

from app.models import Policy, PaymentRecord


class PaymentError(Exception):
    def __init__(self, message: str):
        self.message = message


def _generate_order_no() -> str:
    now = datetime.datetime.now()
    return f"ORD{now.strftime('%Y%m%d%H%M%S')}{now.microsecond % 10000:04d}"


def create_payment_order(db: Session, policy_id: int, callback_url: str) -> PaymentRecord:
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise PaymentError("保单不存在")
    if policy.status != "active":
        raise PaymentError("保单状态异常，无法支付")

    existing = (
        db.query(PaymentRecord)
        .filter(PaymentRecord.policy_id == policy_id, PaymentRecord.status == "pending")
        .first()
    )
    if existing:
        return existing

    order_no = _generate_order_no()
    record = PaymentRecord(
        policy_id=policy_id,
        order_no=order_no,
        amount=policy.product.premium,
        callback_url=callback_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


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

    # Notify frontend callback
    _send_callback(record)

    return record


def _send_callback(record: PaymentRecord) -> None:
    """Send payment success notification to the frontend callback URL (fire-and-forget)."""
    try:
        payload = {
            "order_no": record.order_no,
            "policy_id": record.policy_id,
            "amount": str(record.amount),
            "status": "success",
            "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        }
        httpx.post(record.callback_url, json=payload, timeout=10.0)
    except Exception:
        pass  # fire-and-forget, do not block payment completion
