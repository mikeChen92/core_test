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
    payment_records = relationship("PaymentRecord", back_populates="underwriting")


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


class PaymentRecord(Base):
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    underwriting_id = Column(Integer, ForeignKey("underwriting_records.id"), nullable=False)
    order_no = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SAEnum("pending", "success", "failed", name="payment_status"), default="pending")
    callback_url = Column(String(500), nullable=False)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    underwriting = relationship("UnderwritingRecord", back_populates="payment_records")
