from flask import Flask, jsonify, request
app = Flask(__name__)
_next = 1
BOOKS = [{"id": 1, "title": "Clean Code", "author": "R. Martin", "year": 2000}]
def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)
@app.route("/books", methods=["GET"])
def list_books():
    limit = request.args.get("limit", 100)
    books = BOOKS.copy()
    # (a) Tìm kiếm
    q = request.args.get("q")
    if q:
        q = q.lower()
        books = [
            b for b in books
            if q in b["title"].lower() or q in b["author"].lower()
        ]
    # (b) Sort
    sort = request.args.get("sort")
    if sort in ["title", "author", "year"]:
        books.sort(key=lambda b: b[sort])
    return jsonify(BOOKS[:int(limit)]), 200
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200
@app.route("/books", methods=["POST"])
def create_book():  
    global _next
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    author = body.get("author")
    year = body.get("year")
    if not title or not author:
        return jsonify({"error": "need title+author+year"}), 400
    if not isinstance(year, int) or isinstance(year, bool) or year < 1900:
        return jsonify({"error": "year must be an integer >= 1900"}), 400
    book = {"id": _next, "title": title, "author": author, "year" :year}
    _next += 1
    BOOKS.append(book)
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}
@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    if request.method == "PUT":
        book.update(request.get_json(silent=True) or {})
        return jsonify(book), 200
    BOOKS.remove(book)
    return "", 204
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)