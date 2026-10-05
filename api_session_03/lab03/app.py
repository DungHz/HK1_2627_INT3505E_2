from flask import Flask, request, jsonify
from error import bad_request
import base64
import json

app = Flask(__name__)

ORDERS = [
    {"id": 1, "status": "paid", "customer_id": 101, "total": 120},
    {"id": 2, "status": "pending", "customer_id": 102, "total": 80},
    {"id": 3, "status": "paid", "customer_id": 101, "total": 250},
    {"id": 4, "status": "shipped", "customer_id": 103, "total": 90},
    {"id": 5, "status": "paid", "customer_id": 102, "total": 300},
    {"id": 6, "status": "pending", "customer_id": 101, "total": 70},
    {"id": 7, "status": "paid", "customer_id": 103, "total": 150},
    {"id": 8, "status": "cancelled", "customer_id": 102, "total": 40},
]

ALLOWED_FIELDS = {"id", "status", "customer_id", "total"}
ALLOWED_SORT = {"id", "status", "customer_id", "total"}
ALLOWED_STATUS = {"paid", "pending", "shipped", "cancelled"}


def make_cursor(order_id):
    data = json.dumps({"id": order_id}).encode()
    return base64.urlsafe_b64encode(data).decode()


def read_cursor(cursor):
    try:
        data = base64.urlsafe_b64decode(cursor.encode())
        return json.loads(data.decode())["id"]
    except Exception:
        raise ValueError("cursor not valid")


@app.get("/orders")
def get_orders():
    # limit
    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        return bad_request("limit must a number")

    if limit < 1 or limit > 100:
        return bad_request("limit belong to 1, 100")

    # filter
    orders = ORDERS[:]

    status = request.args.get("status")
    if status:
        if status not in ALLOWED_STATUS:
            return bad_request("status not valid")
        orders = [o for o in orders if o["status"] == status]

    customer_id = request.args.get("customer_id")
    if customer_id:
        try:
            customer_id = int(customer_id)
        except ValueError:
            return bad_request("customer_id must a number")
        orders = [o for o in orders if o["customer_id"] == customer_id]

    # sort
    sort = request.args.get("sort", "id")
    desc = sort.startswith("-")
    sort_field = sort[1:] if desc else sort

    if sort_field not in ALLOWED_SORT:
        return bad_request("not valid")

    orders.sort(key=lambda x: x[sort_field], reverse=desc)

    # cursor
    cursor = request.args.get("cursor")
    if cursor:
        try:
            last_id = read_cursor(cursor)
        except ValueError as e:
            return bad_request(str(e))

        position = next(
            (i for i, order in enumerate(orders) if order["id"] == last_id),
            None
        )

        if position is None:
            return bad_request("cursor unkn")

        orders = orders[position + 1:]

    # lấy page
    page = orders[:limit]
    has_more = len(orders) > limit

    next_cursor = None
    if has_more:
        next_cursor = make_cursor(page[-1]["id"])

    # sparse fieldsets
    fields = request.args.get("fields")
    if fields:
        fields = fields.split(",")

        for field in fields:
            if field not in ALLOWED_FIELDS:
                return bad_request(f"field not valid: {field}")

        page = [
            {field: order[field] for field in fields}
            for order in page
        ]

    return jsonify({
        "data": page,
        "next_cursor": next_cursor,
        "has_more": has_more
    })


if __name__ == "__main__":
    app.run(debug=True)
