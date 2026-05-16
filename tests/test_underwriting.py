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
    assert resp.status_code == 400


def test_underwriting_rejected_duplicate_insured(client, sample_product):
    """Same insured ID number cannot be rejected and then re-submit."""
    # First submission with age > 65 to get rejected
    client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 70,
    })
    # Second submission with valid age but same insured ID
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "UNDERWRITING_REJECTED"


def test_underwriting_age_boundary_18(client, sample_product):
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "小张",
        "insured_id_no": "110101200605052345",
        "insured_age": 18,
    })
    assert resp.status_code == 201


def test_underwriting_age_boundary_65(client, sample_product):
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "老张",
        "insured_id_no": "110101196105052345",
        "insured_age": 65,
    })
    assert resp.status_code == 201


def test_underwriting_invalid_id_number(client, sample_product):
    resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "12345",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    assert resp.status_code == 422
