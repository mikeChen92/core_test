# 保险公司核心系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simple insurance company core system with product scraping, underwriting, policy issuance, and payment modules.

**Architecture:** Layered FastAPI application with api/services/models separation. Product data scraped from 中邮保险 website. Payment simulates a simple checkout flow with callback notification.

**Tech Stack:** Python 3.11+ / FastAPI / MySQL / SQLAlchemy 2.0 / httpx / BeautifulSoup4 / pytest

---

### Task 1: Project Scaffold & Database Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `app/__init__.py`
- Create: `app/database.py`
- Create: `app/models.py`

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pymysql==1.1.1
python-dotenv==1.0.1
httpx==0.27.0
beautifulsoup4==4.12.3
lxml==5.2.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 2: Create `.env`**

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=insurance_core
```

- [ ] **Step 3: Create `app/__init__.py`**

Empty file.

- [ ] **Step 4: Create `app/database.py`**

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "insurance_core")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Create `app/models.py`**

```python
import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, ForeignKey,
    Enum as SAEnum, Numeric
)
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String(200), nullable=False)
    insurance_type = Column(String(100), nullable=False)
    insurance_period = Column(String(100), nullable=False)
    payment_period = Column(String(100), nullable=False)
    sum_insured = Column(Numeric(12, 2), nullable=False)
    premium = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    underwriting_records = relationship("UnderwritingRecord", back_populates="product")
    policies = relationship("Policy", back_populates="product")


class UnderwritingRecord(Base):
    __tablename__ = "underwriting_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    applicant_name = Column(String(100), nullable=False)
    applicant_id_no = Column(String(18), nullable=False)
    insured_name = Column(String(100), nullable=False)
    insured_id_no = Column(String(18), nullable=False)
    insured_age = Column(Integer, nullable=False)
    status = Column(SAEnum("pending", "approved", "rejected", name="uw_status"), default="pending")
    reject_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship("Product", back_populates="underwriting_records")
    policy = relationship("Policy", uselist=False, back_populates="underwriting_record")


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_no = Column(String(50), unique=True, nullable=False)
    underwriting_id = Column(Integer, ForeignKey("underwriting_records.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    status = Column(SAEnum("active", "cancelled", name="policy_status"), default="active")
    effective_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    underwriting_record = relationship("UnderwritingRecord", back_populates="policy")
    product = relationship("Product", back_populates="policies")
    payment_records = relationship("PaymentRecord", back_populates="policy")


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(Integer, ForeignKey("policies.id"), nullable=False)
    order_no = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SAEnum("pending", "success", "failed", name="payment_status"), default="pending")
    callback_url = Column(String(500), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    policy = relationship("Policy", back_populates="payment_records")
```

- [ ] **Step 6: Commit**

```
git add -A && git commit -m "feat: add project scaffold, database config and models"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `app/schemas.py`

- [ ] **Step 1: Write `app/schemas.py`**

```python
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
    policy_id: int
    callback_url: str = Field(..., max_length=500)


class PaymentCreateResponse(BaseModel):
    payment_url: str


class PaymentCallback(BaseModel):
    order_no: str
    status: str


class PaymentResponse(BaseModel):
    id: int
    policy_id: int
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
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat: add pydantic schemas"
```

---

### Task 3: Product Scraper

**Files:**
- Create: `app/scraper/__init__.py`
- Create: `app/scraper/scraper.py`

- [ ] **Step 1: Write `app/scraper/__init__.py`**

Empty file.

- [ ] **Step 2: Write `app/scraper/scraper.py`**

```python
import re
from decimal import Decimal
from typing import Optional
import httpx
from bs4 import BeautifulSoup

SCRAPE_URL = (
    "https://kh.chinapost-life.com/phcs/lcpf/insuredInfo"
    "?goodsCode=ph152335&saleChannelCode=1&saleTypeCode=23"
    "&firstSalePlatformCode=phbx&secondSalePlatformCode=ZYPT000023"
)


class ProductData:
    def __init__(
        self,
        product_name: str,
        insurance_type: str,
        insurance_period: str,
        payment_period: str,
        sum_insured: Decimal,
        premium: Decimal,
    ):
        self.product_name = product_name
        self.insurance_type = insurance_type
        self.insurance_period = insurance_period
        self.payment_period = payment_period
        self.sum_insured = sum_insured
        self.premium = premium


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _extract_value_text(soup: BeautifulSoup, label_text: str) -> Optional[str]:
    """Find a label element containing label_text and return the adjacent value span."""
    label = soup.find("span", string=re.compile(re.escape(label_text)))
    if not label:
        return None
    value_span = label.find_next("span", class_=re.compile(r"value|content|text", re.I))
    if value_span:
        return _clean_text(value_span.get_text(strip=True))
    parent = label.find_parent("li") or label.find_parent("div", class_=re.compile(r"item|field|row", re.I))
    if parent:
        all_spans = parent.find_all("span")
        for s in all_spans:
            if s != label:
                return _clean_text(s.get_text(strip=True))
    return None


def _parse_decimal(text: Optional[str]) -> Optional[Decimal]:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text)
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def scrape_product() -> ProductData:
    """Scrape product info from 中邮保险 webpage."""
    response = httpx.get(SCRAPE_URL, timeout=30.0, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    product_name = _clean_text(soup.title.get_text(strip=True)) if soup.title else "中邮普惠保险"

    fields = {}
    label_map = {
        "product_name": ["产品名称"],
        "insurance_type": ["险种"],
        "insurance_period": ["保险期间", "保障期间"],
        "payment_period": ["缴费期间", "交费期间"],
        "sum_insured": ["保额", "保险金额"],
        "premium": ["保费", "保险费"],
    }

    for key, labels in label_map.items():
        for lbl in labels:
            val = _extract_value_text(soup, lbl)
            if val:
                fields[key] = val
                break

    sum_insured = _parse_decimal(fields.get("sum_insured"))
    premium = _parse_decimal(fields.get("premium"))

    return ProductData(
        product_name=fields.get("product_name", product_name),
        insurance_type=fields.get("insurance_type", "普惠保险"),
        insurance_period=fields.get("insurance_period", ""),
        payment_period=fields.get("payment_period", ""),
        sum_insured=sum_insured or Decimal("0"),
        premium=premium or Decimal("0"),
    )
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add product scraper"
```

---

### Task 4: Product API Routes

**Files:**
- Create: `app/api/__init__.py`
- Create: `app/api/products.py`

- [ ] **Step 1: Write `app/api/__init__.py`**

Empty file.

- [ ] **Step 2: Write `app/api/products.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse, ProductListResponse, ErrorDetail
from app.scraper.scraper import scrape_product, SCRAPE_URL

router = APIRouter(prefix="/api/products", tags=["products"])


@router.post("/scrape", response_model=ProductResponse)
def scrape_and_save(db: Session = Depends(get_db)):
    """Scrape product info from webpage and save to database."""
    try:
        data = scrape_product()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"code": "SCRAPE_FAILED", "message": f"抓取产品信息失败: {str(e)}"},
        )

    # Replace existing product data (only one product)
    existing = db.query(Product).first()
    if existing:
        existing.product_name = data.product_name
        existing.insurance_type = data.insurance_type
        existing.insurance_period = data.insurance_period
        existing.payment_period = data.payment_period
        existing.sum_insured = data.sum_insured
        existing.premium = data.premium
        product = existing
    else:
        product = Product(
            product_name=data.product_name,
            insurance_type=data.insurance_type,
            insurance_period=data.insurance_period,
            payment_period=data.payment_period,
            sum_insured=data.sum_insured,
            premium=data.premium,
        )
        db.add(product)

    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=ProductListResponse)
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return {"products": products}


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail={"code": "PRODUCT_NOT_FOUND", "message": "产品不存在"},
        )
    return product
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add product API routes"
```

---

### Task 5: Underwriting Service & API

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/underwriting.py`
- Create: `app/api/underwriting.py`

- [ ] **Step 1: Write `app/services/__init__.py`**

Empty file.

- [ ] **Step 2: Write `app/services/underwriting.py`**

```python
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
```

- [ ] **Step 3: Write `app/api/underwriting.py`**

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: add underwriting service and API"
```

---

### Task 6: Policy Service & API

**Files:**
- Create: `app/services/policy.py`
- Create: `app/api/policies.py`

- [ ] **Step 1: Write `app/services/policy.py`**

```python
import datetime

from sqlalchemy.orm import Session

from app.models import UnderwritingRecord, Policy


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
```

- [ ] **Step 2: Write `app/api/policies.py`**

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add -A && git commit -m "feat: add policy service and API"
```

---

### Task 7: Payment Service & API & Checkout Page

**Files:**
- Create: `app/services/payment.py`
- Create: `app/api/payments.py`
- Create: `app/templates/checkout.html`

- [ ] **Step 1: Write `app/services/payment.py`**

```python
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
```

- [ ] **Step 2: Write `app/api/payments.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

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
```

- [ ] **Step 3: Write checkout page route in `app/api/payments.py`** (append to file)

Add a checkout page route and payment confirmation endpoint:

```python
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)


@router.get("/payment/{order_no}", response_class=HTMLResponse, include_in_schema=False)
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


@router.post("/payment/{order_no}/confirm", include_in_schema=False)
def confirm_payment(order_no: str, db: Session = Depends(get_db)):
    """User clicks 'confirm payment' on checkout page."""
    try:
        record = complete_payment(db, order_no)
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=e.message)

    redirect_url = f"{record.callback_url}?order_no={record.order_no}&status=success"
    return RedirectResponse(url=redirect_url)
```

- [ ] **Step 4: Write `app/templates/checkout.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>支付收银台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f7fa;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh; color: #333;
        }
        .checkout-card {
            background: #fff;
            border-radius: 12px;
            padding: 40px;
            width: 420px;
            box-shadow: 0 2px 16px rgba(0,0,0,0.08);
        }
        .checkout-card h1 {
            font-size: 22px; margin-bottom: 24px; text-align: center;
        }
        .info-row {
            display: flex; justify-content: space-between;
            padding: 12px 0; border-bottom: 1px solid #eee;
        }
        .info-row .label { color: #888; font-size: 14px; }
        .info-row .value { font-weight: 600; font-size: 14px; }
        .amount-row {
            display: flex; justify-content: space-between;
            padding: 20px 0; margin-top: 8px;
        }
        .amount-row .label { font-size: 16px; color: #888; }
        .amount-row .value { font-size: 28px; font-weight: 700; color: #e4393c; }
        .pay-btn {
            width: 100%; padding: 14px; font-size: 18px;
            background: #e4393c; color: #fff; border: none;
            border-radius: 8px; cursor: pointer; margin-top: 8px;
        }
        .pay-btn:hover { background: #c9302c; }
        .pay-btn:disabled { background: #ccc; cursor: not-allowed; }
        .error-msg { color: #e4393c; text-align: center; margin-top: 12px; display: none; }
    </style>
</head>
<body>
    <div class="checkout-card">
        <h1>支付收银台</h1>
        <div class="info-row">
            <span class="label">订单号</span>
            <span class="value" id="orderNo">{{ order_no }}</span>
        </div>
        <div class="info-row">
            <span class="label">保单号</span>
            <span class="value">{{ policy_no }}</span>
        </div>
        <div class="amount-row">
            <span class="label">支付金额</span>
            <span class="value">¥{{ amount }}</span>
        </div>
        <button class="pay-btn" id="payBtn" onclick="confirmPay()">确认支付</button>
        <div class="error-msg" id="errorMsg">支付失败，请重试</div>
    </div>
    <script>
        async function confirmPay() {
            const btn = document.getElementById('payBtn');
            const error = document.getElementById('errorMsg');
            btn.disabled = true;
            error.style.display = 'none';
            try {
                const resp = await fetch(window.location.pathname + '/confirm', { method: 'POST' });
                if (resp.redirected) {
                    window.location.href = resp.url;
                } else if (!resp.ok) {
                    const err = await resp.text();
                    error.textContent = err || '支付失败，请重试';
                    error.style.display = 'block';
                    btn.disabled = false;
                }
            } catch (e) {
                error.textContent = '网络错误，请重试';
                error.style.display = 'block';
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: add payment service, API and checkout page"
```

---

### Task 8: Main App Entry Point & Wiring

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: Write `app/main.py`**

```python
from fastapi import FastAPI
from app.database import engine, Base
from app.api import products, underwriting, policies, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="保险公司核心系统", version="1.0.0")

app.include_router(products.router)
app.include_router(underwriting.router)
app.include_router(policies.router)
app.include_router(payments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 2: Commit**

```bash
git add -A && git commit -m "feat: add main app entry point"
```

---

### Task 9: Tests

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_products.py`
- Create: `tests/test_underwriting.py`
- Create: `tests/test_policies.py`
- Create: `tests/test_payments.py`

- [ ] **Step 1: Write `tests/__init__.py`**

Empty file.

- [ ] **Step 2: Write `tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import Product
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_product(db):
    product = Product(
        product_name="中邮普惠保险",
        insurance_type="普惠保险",
        insurance_period="1年",
        payment_period="一次性缴清",
        sum_insured=100000.00,
        premium=100.00,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
```

- [ ] **Step 3: Write `tests/test_products.py`**

```python
from unittest.mock import patch, MagicMock
from app.scraper.scraper import ProductData


def test_list_products_empty(client):
    resp = client.get("/api/products")
    assert resp.status_code == 200
    assert resp.json() == {"products": []}


def test_get_product_not_found(client):
    resp = client.get("/api/products/999")
    assert resp.status_code == 404


def test_list_products_with_data(client, sample_product):
    resp = client.get("/api/products")
    data = resp.json()
    assert len(data["products"]) == 1
    assert data["products"][0]["product_name"] == "中邮普惠保险"


def test_get_product(client, sample_product):
    resp = client.get(f"/api/products/{sample_product.id}")
    assert resp.status_code == 200
    assert resp.json()["product_name"] == "中邮普惠保险"


@patch("app.api.products.scrape_product")
def test_scrape_product(mock_scrape, client, db):
    mock_scrape.return_value = ProductData(
        product_name="测试产品",
        insurance_type="健康险",
        insurance_period="1年",
        payment_period="月缴",
        sum_insured=50000.00,
        premium=200.00,
    )
    resp = client.post("/api/products/scrape")
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_name"] == "测试产品"
    assert float(data["premium"]) == 200.00


@patch("app.api.products.scrape_product")
def test_scrape_product_overwrites_existing(mock_scrape, client, sample_product):
    mock_scrape.return_value = ProductData(
        product_name="新产品", insurance_type="寿险", insurance_period="10年",
        payment_period="年缴", sum_insured=200000.00, premium=500.00,
    )
    resp = client.post("/api/products/scrape")
    assert resp.status_code == 200
    assert resp.json()["product_name"] == "新产品"

    # Verify only one product
    resp2 = client.get("/api/products")
    assert len(resp2.json()["products"]) == 1


@patch("app.api.products.scrape_product")
def test_scrape_failure_returns_502(mock_scrape, client):
    mock_scrape.side_effect = Exception("Connection error")
    resp = client.post("/api/products/scrape")
    assert resp.status_code == 502
```

- [ ] **Step 4: Write `tests/test_underwriting.py`**

```python
def test_submit_underwriting_success(client, sample_product):
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "approved"
    assert data["applicant_name"] == "张三"


def test_submit_underwriting_age_out_of_range(client, sample_product):
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199005052345",
        "insured_age": 70,
    })
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "UNDERWRITING_REJECTED"


def test_get_underwriting(client, sample_product):
    # Create first
    create_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    uw_id = create_resp.json()["id"]

    resp = client.get(f"/api/underwriting/{uw_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


def test_get_underwriting_not_found(client):
    resp = client.get("/api/underwriting/999")
    assert resp.status_code == 404


def test_underwriting_missing_product(client):
    resp = client.post("/api/underwriting", json={
        "product_id": 999,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199005052345",
        "insured_age": 30,
    })
    # Product not found -> underwriting rejects due to missing product
    # The service raises UnderwritingError which becomes 400
    assert resp.status_code == 400
```

- [ ] **Step 5: Write `tests/test_policies.py`**

```python
def test_create_policy_success(client, sample_product):
    # Create underwriting first
    uw_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    uw_id = uw_resp.json()["id"]

    resp = client.post("/api/policies", json={"underwriting_id": uw_id})
    assert resp.status_code == 201
    data = resp.json()
    assert data["policy_no"].startswith("P")
    assert data["status"] == "active"
    assert data["underwriting_id"] == uw_id


def test_create_policy_twice_fails(client, sample_product):
    uw_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    uw_id = uw_resp.json()["id"]

    client.post("/api/policies", json={"underwriting_id": uw_id})
    resp2 = client.post("/api/policies", json={"underwriting_id": uw_id})
    assert resp2.status_code == 400
    assert resp2.json()["detail"]["code"] == "POLICY_ERROR"


def test_create_policy_not_approved(client, sample_product):
    # Create a rejected underwriting (age > 65)
    uw_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "老人",
        "insured_id_no": "110101195001012345",
        "insured_age": 70,
    })
    assert uw_resp.status_code == 400  # Rejected at underwriting

    # Can't create policy without an approved underwriting
    resp = client.post("/api/policies", json={"underwriting_id": 999})
    assert resp.status_code == 400


def test_get_policy(client, sample_product):
    uw_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    policy_resp = client.post("/api/policies", json={"underwriting_id": uw_resp.json()["id"]})
    policy_id = policy_resp.json()["id"]

    resp = client.get(f"/api/policies/{policy_id}")
    assert resp.status_code == 200


def test_list_policies(client, sample_product):
    resp = client.get("/api/policies")
    assert resp.status_code == 200


def test_get_policy_not_found(client):
    resp = client.get("/api/policies/999")
    assert resp.status_code == 404
```

- [ ] **Step 6: Write `tests/test_payments.py`**

```python
def test_create_payment(client, sample_product):
    # Full flow: underwriting -> policy -> payment
    uw = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    }).json()
    policy = client.post("/api/policies", json={"underwriting_id": uw["id"]}).json()

    resp = client.post("/api/payments/create", json={
        "policy_id": policy["id"],
        "callback_url": "http://example.com/callback",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_url"].startswith("/payment/")


def test_confirm_payment(client, sample_product):
    uw = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    }).json()
    policy = client.post("/api/policies", json={"underwriting_id": uw["id"]}).json()
    payment = client.post("/api/payments/create", json={
        "policy_id": policy["id"],
        "callback_url": "http://example.com/callback",
    }).json()

    order_no = payment["payment_url"].split("/")[-1]

    resp = client.post(f"/api/payments/callback", json={
        "order_no": order_no,
        "status": "success",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_get_payment(client, sample_product):
    uw = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    }).json()
    policy = client.post("/api/policies", json={"underwriting_id": uw["id"]}).json()
    client.post("/api/payments/create", json={
        "policy_id": policy["id"],
        "callback_url": "http://example.com/callback",
    })

    resp = client.get("/api/payments/1")
    assert resp.status_code == 200
    assert resp.json()["policy_id"] == policy["id"]
```

- [ ] **Step 7: Run all tests and verify**

```bash
cd /Users/mike/ClaudeProjects/projects/core_test && python -m pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "test: add integration tests for all modules"
```

---

### Task 10: Run Checkout Page Tests (Manual Verification)

- [ ] **Step 1: Start the server**

```bash
cd /Users/mike/ClaudeProjects/projects/core_test && uvicorn app.main:app --reload
```

- [ ] **Step 2: Verify health endpoint**

```bash
curl http://localhost:8000/health
```
Expected: `{"status": "ok"}`

- [ ] **Step 3: Verify API docs available**

Open `http://localhost:8000/docs` in browser.

---

## Self-Review Checklist

- **Spec coverage:** Every requirement from the spec has a corresponding task:
  - Product scraper → Task 3
  - Product API → Task 4
  - Underwriting service + API → Task 5
  - Policy service + API → Task 6
  - Payment service + API + checkout page → Task 7
  - Database models → Task 1
  - Schemas → Task 2
  - Main app wiring → Task 8
  - Tests → Task 9

- **Placeholder scan:** No "TBD", "TODO", or incomplete placeholders. Every step has complete code.

- **Type consistency:** All method signatures and property names are consistent across tasks. `order_no` in payment tasks matches across service, API, and tests.
