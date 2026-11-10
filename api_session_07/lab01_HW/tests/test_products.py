def create_product(client, *, sku="KB-001", name="Keyboard", price=125000, stock=10):
    return client.post("/api/v1/products", json={
        "sku": sku,
        "name": name,
        "price_cents": price,
        "qty_in_stock": stock,
    })


def test_create_product_and_list(client):
    response = create_product(client)
    assert response.status_code == 201
    assert response.json["sku"] == "KB-001"

    listing = client.get("/api/v1/products?page=1&size=20")
    assert listing.status_code == 200
    assert listing.json["total"] == 1
    assert listing.json["items"][0]["name"] == "Keyboard"


def test_duplicate_sku_returns_409(client):
    assert create_product(client).status_code == 201
    duplicate = create_product(client, name="Another keyboard")
    assert duplicate.status_code == 409
    assert duplicate.json["code"] == "conflict"


def test_reserve_cannot_make_stock_negative(client):
    product = create_product(client, stock=2).json

    response = client.post(f"/api/v1/products/{product['id']}/reserve", json={"qty": 3})
    assert response.status_code == 409
    assert response.json["code"] == "out_of_stock"

    current = client.get(f"/api/v1/products/{product['id']}")
    assert current.json["qty_in_stock"] == 2


def test_delete_is_soft_delete(client):
    product = create_product(client).json
    response = client.delete(f"/api/v1/products/{product['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/v1/products/{product['id']}").status_code == 404
    assert client.get("/api/v1/products").json["total"] == 0
