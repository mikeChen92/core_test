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


def test_payment_nonexistent_policy(client):
    resp = client.post("/api/payments/create", json={
        "policy_id": 999,
        "callback_url": "http://example.com/callback",
    })
    assert resp.status_code == 400


def test_payment_callback_failed_status(client, sample_product):
    uw = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    }).json()
    policy = client.post("/api/policies", json={"underwriting_id": uw["id"]}).json()
    pay = client.post("/api/payments/create", json={
        "policy_id": policy["id"],
        "callback_url": "http://example.com/callback",
    }).json()
    order_no = pay["payment_url"].split("/")[-1]

    resp = client.post("/api/payments/callback", json={
        "order_no": order_no,
        "status": "failed",
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"


def test_payment_callback_nonexistent_order(client):
    resp = client.post("/api/payments/callback", json={
        "order_no": "NONEXISTENT",
        "status": "failed",
    })
    assert resp.status_code == 400


def test_confirm_already_completed_payment(client, sample_product):
    uw = client.post("/api/underwriting", json={
        "product_id": sample_product.id,
        "applicant_name": "张三",
        "applicant_id_no": "110101199001011234",
        "insured_name": "李四",
        "insured_id_no": "110101199505052345",
        "insured_age": 30,
    }).json()
    policy = client.post("/api/policies", json={"underwriting_id": uw["id"]}).json()
    pay = client.post("/api/payments/create", json={
        "policy_id": policy["id"],
        "callback_url": "http://example.com/callback",
    }).json()
    order_no = pay["payment_url"].split("/")[-1]

    # Complete payment
    client.post("/api/payments/callback", json={"order_no": order_no, "status": "success"})

    # Try to complete again
    resp = client.post("/api/payments/callback", json={"order_no": order_no, "status": "success"})
    assert resp.status_code == 400
