from flask import Flask, jsonify, request
app = Flask(__name__)
ORDERS = {
    "1": {"id": "1", "status": "pending"},
    "2": {"id": "2", "status": "shipped"},
    "3": {"id": "3", "status": "delivered"}
}
# GET - all order
@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(list(ORDERS.values())), 200
# GET - one order
@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify({"error": "not found"}), 404

    return jsonify(order), 200

# POST - new order
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON lỗi"}), 400
    order_id = str(len(ORDERS) + 1)
    order = {
        "id": order_id,
        "status": data.get("status", "pending")
    }
    ORDERS[order_id] = order
    return jsonify(order), 201

# DELETE
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    # 404
    order = ORDERS.get(order_id)
    if order is None:
        return jsonify({"error": "not found"}), 404
    # 409 
    if order["status"] in ("shipped", "delivered"):
        return jsonify({"error": "cannot delete"}), 409
    del ORDERS[order_id]
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)