from flask import Flask, jsonify, request, make_response
app = Flask(__name__)
BOOKS = []
_next_id = 1
# ─── GET /books ───
@app.get("/books")
def list_books():
    return jsonify({
        "data": BOOKS,
        "total": len(BOOKS)
    }), 200
# ─── POST /books ───
@app.post("/books")
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()
    if not t or not a:
        return jsonify(error="title and author required"), 422
    book = {
        "id": _next_id,
        "title": t,
        "author": a
    }
    BOOKS.append(book)
    _next_id += 1
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp
# ─── GET /books/<id> ─── cache 60s
@app.get("/books/<int:bid>")
def fetch(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )
    if i is None:
        return jsonify(error="not found"), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"] = "max-age=60"
    return resp
# ─── PUT ─── thay toàn bộ, title + author bắt buộc
@app.put("/books/<int:bid>")
def put(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )
    if i is None:
        return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    t = p.get("title")
    a = p.get("author")
    if not t or not a:
        return jsonify(error="need title+author"), 422
    BOOKS[i] = {
        "id": bid,
        "title": t.strip(),
        "author": a.strip(),
        "isbn": p.get("isbn"),
        "price": p.get("price")
    }
    return jsonify(BOOKS[i]), 200
# ─── PATCH ─── chỉ cập nhật field có trong body
@app.patch("/books/<int:bid>")
def patch(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )
    if i is None:
        return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    if "price" in p:
        if not isinstance(p["price"], (int, float)) or p["price"] < 0:
            return jsonify(error="price must be positive"), 422
    for k in "title author isbn price".split():
        if k in p:
            BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200
# ─── DELETE ───
@app.delete("/books/<int:bid>")
def delete(bid):
    i = next(
        (k for k, b in enumerate(BOOKS) if b["id"] == bid),
        None
    )
    if i is None:
        return jsonify(error="not found"), 404
    BOOKS.pop(i)
    return "", 204
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)