def sample_product(**overrides):
    payload = {
        "sku": "KEY-001",
        "name": "Mechanical Keyboard",
        "category": "Electronics",
        "description": "USB keyboard",
        "price": 2500.0,
        "quantity": 10,
        "reorder_level": 3,
    }
    payload.update(overrides)
    return payload

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_and_list_product(client):
    response = client.post("/api/products", json=sample_product())
    assert response.status_code == 201
    assert response.json()["sku"] == "KEY-001"
    assert response.json()["quantity"] == 10
    listing = client.get("/api/products")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

def test_duplicate_sku_is_rejected(client):
    assert client.post("/api/products", json=sample_product()).status_code == 201
    response = client.post("/api/products", json=sample_product(name="Another keyboard"))
    assert response.status_code == 409

def test_invalid_price_is_rejected(client):
    response = client.post("/api/products", json=sample_product(price=-1))
    assert response.status_code == 422

def test_stock_adjustment_and_movement_history(client):
    created = client.post("/api/products", json=sample_product(quantity=10)).json()
    response = client.post(f"/api/products/{created['id']}/stock", json={
        "change": -3, "reason": "sale", "note": "Order #100"
    })
    assert response.status_code == 201
    assert response.json()["change"] == -3
    product = client.get(f"/api/products/{created['id']}").json()
    assert product["quantity"] == 7
    movements = client.get(f"/api/products/{created['id']}/movements").json()
    assert len(movements) == 2  # opening stock plus adjustment

def test_stock_cannot_become_negative(client):
    created = client.post("/api/products", json=sample_product(quantity=2)).json()
    response = client.post(f"/api/products/{created['id']}/stock", json={
        "change": -5, "reason": "sale", "note": ""
    })
    assert response.status_code == 400
    assert client.get(f"/api/products/{created['id']}").json()["quantity"] == 2

def test_dashboard_metrics(client):
    client.post("/api/products", json=sample_product(quantity=10, price=100, reorder_level=3))
    client.post("/api/products", json=sample_product(
        sku="MOUSE-001", name="Mouse", quantity=2, price=50, reorder_level=5
    ))
    data = client.get("/api/dashboard").json()
    assert data["total_products"] == 2
    assert data["total_units"] == 12
    assert data["inventory_value"] == 1100.0
    assert data["low_stock_count"] == 1

def test_search_and_low_stock_filter(client):
    client.post("/api/products", json=sample_product(quantity=10))
    client.post("/api/products", json=sample_product(
        sku="MOUSE-001", name="Mouse", quantity=1, reorder_level=3
    ))
    assert len(client.get("/api/products?search=mouse").json()) == 1
    assert len(client.get("/api/products?low_stock=true").json()) == 1

def test_update_and_delete(client):
    created = client.post("/api/products", json=sample_product()).json()
    updated = client.patch(f"/api/products/{created['id']}", json={"name":"Updated Keyboard"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Keyboard"
    deleted = client.delete(f"/api/products/{created['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/products/{created['id']}").status_code == 404

def test_quantity_cannot_be_changed_by_general_update(client):
    created = client.post("/api/products", json=sample_product()).json()
    response = client.patch(f"/api/products/{created['id']}", json={"quantity": 99})
    assert response.status_code == 400
