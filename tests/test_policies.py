def test_create_policy_success(client, sample_product):
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


def test_create_policy_nonexistent_underwriting(client):
    resp = client.post("/api/policies", json={"underwriting_id": 999})
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "POLICY_ERROR"
