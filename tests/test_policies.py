def test_create_policy_without_payment(client, sample_product):
    """承保需要先支付，未支付时拒绝出单"""
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
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "POLICY_ERROR"
    assert "未支付" in resp.json()["detail"]["message"]


def test_create_policy_success(client, sample_product):
    """核保通过 → 支付 → 承保成功"""
    uw_resp = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    })
    uw_id = uw_resp.json()["id"]

    # 先支付
    pay = client.post("/api/payments/create", json={
        "underwriting_id": uw_id,
        "callback_url": "http://example.com/callback",
    }).json()
    order_no = pay["payment_url"].split("/")[-1]
    client.post("/api/payments/callback", json={"order_no": order_no, "status": "success"})

    # 再承保
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

    # 先支付
    pay = client.post("/api/payments/create", json={
        "underwriting_id": uw_id,
        "callback_url": "http://example.com/callback",
    }).json()
    order_no = pay["payment_url"].split("/")[-1]
    client.post("/api/payments/callback", json={"order_no": order_no, "status": "success"})

    # 第一次承保成功
    client.post("/api/policies", json={"underwriting_id": uw_id})
    # 第二次承保失败
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
    uw_id = uw_resp.json()["id"]

    pay = client.post("/api/payments/create", json={
        "underwriting_id": uw_id,
        "callback_url": "http://example.com/callback",
    }).json()
    order_no = pay["payment_url"].split("/")[-1]
    client.post("/api/payments/callback", json={"order_no": order_no, "status": "success"})

    policy_resp = client.post("/api/policies", json={"underwriting_id": uw_id})
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
