from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import PaymentRecord
from app.schemas import (
    PaymentCreate,
    PaymentCreateResponse,
    PaymentCallback,
    PaymentResponse,
    ErrorDetail,
)
from app.services.payment import create_payment_order, complete_payment, PaymentError

router = APIRouter(prefix="/api/payments", tags=["payments"])
page_router = APIRouter(prefix="", tags=["payment_pages"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.post("/create", response_model=PaymentCreateResponse)
def create_payment(data: PaymentCreate, db: Session = Depends(get_db)):
    try:
        record = create_payment_order(db, data.policy_id, data.callback_url)
    except PaymentError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "PAYMENT_ERROR", "message": e.message},
        )
    return PaymentCreateResponse(payment_url=f"/payment/{record.order_no}")


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.id == payment_id).first()
    if not record:
        raise HTTPException(
            status_code=404,
            detail={"code": "PAYMENT_NOT_FOUND", "message": "支付记录不存在"},
        )
    return record


@router.post("/callback", response_model=PaymentResponse)
def payment_callback(data: PaymentCallback, db: Session = Depends(get_db)):
    """External callback: mark payment as success/failed."""
    try:
        if data.status == "success":
            record = complete_payment(db, data.order_no)
        else:
            record = db.query(PaymentRecord).filter(
                PaymentRecord.order_no == data.order_no
            ).first()
            if record:
                record.status = "failed"
                db.commit()
                db.refresh(record)
    except PaymentError as e:
        raise HTTPException(
            status_code=400,
            detail={"code": "PAYMENT_ERROR", "message": e.message},
        )
    return record


@page_router.get("/payment/{order_no}", response_class=HTMLResponse, include_in_schema=False)
def checkout_page(order_no: str, request: Request, db: Session = Depends(get_db)):
    record = db.query(PaymentRecord).filter(PaymentRecord.order_no == order_no).first()
    if not record:
        raise HTTPException(status_code=404, detail="支付订单不存在")
    policy = record.policy
    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "order_no": order_no,
            "policy_no": policy.policy_no,
            "amount": f"{record.amount:.2f}",
            "callback_url": record.callback_url,
        },
    )


@page_router.post("/payment/{order_no}/confirm", include_in_schema=False)
def confirm_payment(order_no: str, db: Session = Depends(get_db)):
    """User clicks 'confirm payment' on checkout page."""
    try:
        record = complete_payment(db, order_no)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=e.message)

    redirect_url = f"{record.callback_url}?order_no={record.order_no}&status=success"
    return RedirectResponse(url=redirect_url)
