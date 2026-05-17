import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# --- Product ---
class ProductResponse(BaseModel):
    id: int
    product_name: str
    insurance_type: str
    insurance_period: str
    payment_period: str
    sum_insured: Decimal
    premium: Decimal
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    products: list[ProductResponse]


# --- Underwriting ---
class UnderwritingCreate(BaseModel):
    product_id: int
    applicant_name: str = Field(..., min_length=1, max_length=100)
    applicant_id_no: str = Field(..., pattern=r"^\d{17}[\dXx]$")
    insured_name: str = Field(..., min_length=1, max_length=100)
    insured_id_no: str = Field(..., pattern=r"^\d{17}[\dXx]$")
    insured_age: int = Field(..., ge=0, le=150)


class UnderwritingResponse(BaseModel):
    id: int
    product_id: int
    applicant_name: str
    insured_name: str
    insured_age: int
    status: str
    reject_reason: Optional[str] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Policy ---
class PolicyCreate(BaseModel):
    underwriting_id: int


class PolicyResponse(BaseModel):
    id: int
    policy_no: str
    underwriting_id: int
    product_id: int
    status: str
    effective_date: datetime.date
    expiry_date: datetime.date
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PolicyListResponse(BaseModel):
    policies: list[PolicyResponse]


# --- Payment ---
class PaymentCreate(BaseModel):
    underwriting_id: int
    callback_url: str = Field(..., max_length=500)


class PaymentCreateResponse(BaseModel):
    payment_url: str


class PaymentCallback(BaseModel):
    order_no: str
    status: str


class PaymentResponse(BaseModel):
    id: int
    underwriting_id: int
    order_no: str
    amount: Decimal
    status: str
    callback_url: str
    paid_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Error ---
class ErrorResponse(BaseModel):
    detail: dict


class ErrorDetail(BaseModel):
    code: str
    message: str
