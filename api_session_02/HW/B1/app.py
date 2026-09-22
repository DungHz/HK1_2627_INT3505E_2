import sqlite3
from flask import Flask, jsonify, request, make_response
app = Flask(__name__)
def get_db_connection():
    conn = sqlite3.connect('orders.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()
init_db()

@app.post("/orders")
def create_order():
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    data = request.get_json(silent=True) or {}
    item_name = data.get("item_name")
    quantity = data.get("quantity")
    if not item_name or not quantity:
        return jsonify(error="item_name and quantity required"), 422
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (item_name, quantity) VALUES (?, ?)', (item_name, quantity))
    conn.commit()
    order_id = cursor.lastrowid
    conn.close()
    resp = make_response(jsonify({"id": order_id, "item_name": item_name, "quantity": quantity}), 201)
    resp.headers["Location"] = f"/orders/{order_id}"
    return resp

@app.get("/orders")
def list_orders():
    conn = get_db_connection()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    conn.close()
    
    return jsonify({
        "data": [dict(ix) for ix in orders],
        "total": len(orders)
    }), 200

@app.get("/orders/<int:oid>")
def get_order(oid):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (oid,)).fetchone()
    conn.close()
    
    if order is None:
        return jsonify(error="not found"), 404
        
    return jsonify(dict(order)), 200

if __name__ == '__main__':
    app.run(debug=True)