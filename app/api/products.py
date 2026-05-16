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
