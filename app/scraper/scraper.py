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
