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
