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
