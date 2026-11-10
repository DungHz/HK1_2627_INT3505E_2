from sqlalchemy import event

from product_api.extensions import db


def create_product(client, sku, name, price, stock):
    response = client.post("/api/v1/products", json={
        "sku": sku,
        "name": name,
        "price_cents": price,
        "qty_in_stock": stock,
    })
    assert response.status_code == 201
    return response.json


def test_post_order_supports_multiple_products_and_decrements_stock(client):
    keyboard = create_product(client, "KB-001", "Keyboard", 125000, 10)
    mouse = create_product(client, "MS-001", "Mouse", 55000, 5)

    response = client.post("/api/v1/orders", json={
        "items": [
            {"product_id": keyboard["id"], "quantity": 2},
            {"product_id": mouse["id"], "quantity": 1},
        ]
    })

    assert response.status_code == 201
    assert len(response.json["items"]) == 2
    assert {item["product"]["sku"] for item in response.json["items"]} == {
        "KB-001", "MS-001"
    }
    assert client.get(f"/api/v1/products/{keyboard['id']}").json["qty_in_stock"] == 8
    assert client.get(f"/api/v1/products/{mouse['id']}").json["qty_in_stock"] == 4


def test_order_creation_rolls_back_all_stock_when_one_item_is_out_of_stock(client):
    keyboard = create_product(client, "KB-001", "Keyboard", 125000, 10)
    mouse = create_product(client, "MS-001", "Mouse", 55000, 1)

    response = client.post("/api/v1/orders", json={
        "items": [
            {"product_id": keyboard["id"], "quantity": 2},
            {"product_id": mouse["id"], "quantity": 2},
        ]
    })

    assert response.status_code == 409
    assert client.get(f"/api/v1/products/{keyboard['id']}").json["qty_in_stock"] == 10
    assert client.get(f"/api/v1/products/{mouse['id']}").json["qty_in_stock"] == 1
    assert client.get("/api/v1/orders").json["total"] == 0


def test_get_order_uses_eager_loading_without_n_plus_one(app, client):
    first = create_product(client, "KB-001", "Keyboard", 125000, 10)
    second = create_product(client, "MS-001", "Mouse", 55000, 5)
    created = client.post("/api/v1/orders", json={
        "items": [
            {"product_id": first["id"], "quantity": 1},
            {"product_id": second["id"], "quantity": 2},
        ]
    })
    assert created.status_code == 201
    order_id = created.json["id"]

    statements = []

    def count_selects(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    with app.app_context():
        engine = db.engine
        event.listen(engine, "before_cursor_execute", count_selects)
        try:
            response = client.get(f"/api/v1/orders/{order_id}")
        finally:
            event.remove(engine, "before_cursor_execute", count_selects)

    assert response.status_code == 200
    assert len(response.json["items"]) == 2
    # selectinload(Order.items) + joinedload(OrderItem.product): 2 SELECTs,
    # not 1 + N queries when serializing each order item and its product.
    assert len(statements) == 2
