from flask import Flask, jsonify, request, make_response
app = Flask(__name__)
BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "R. Martin"},
    {"id": 2, "title": "DDIA", "author": "Kleppmann"},
    {"id": 3, "title": "Python Basic", "author": "Nguyen Van A"},
    {"id": 4, "title": "Flask Web", "author": "Nguyen Van A"}
]
DEFAULT_SIZE, MAX_SIZE = 20, 100
# ─── GET /books ───
@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="page and size must be int"), 400
    page = max(page, 1)
    size = max(min(size, MAX_SIZE), 1)
    flt = BOOKS
    a = request.args.get("author")
    if a:
        flt = [b for b in flt if b["author"].lower() == a.lower()]
    q = (request.args.get("q") or "").lower()
    if q:
        flt = [b for b in flt if q in b["title"].lower()]
    total = len(flt)
    start = (page - 1) * size
    end = start + size
    items = flt[start:end]
    last = (total + size - 1) // size
    def u(p):
        return f"/books?page={p}&size={size}"
    links = {"self": {"href": u(page)}, "first": {"href": u(1)}, "last": {"href": u(max(last, 1))}}
    if page > 1:
        links["prev"] = {"href": u(page - 1)}
    if end < total:
        links["next"] = {"href": u(page + 1)}
    body = {"data": items, "pagination": {"page": page, "size": size, "total": total, "total_pages": last}, "_links": links}
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)