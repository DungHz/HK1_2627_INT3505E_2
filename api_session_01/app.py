from flask import Flask, jsonify, request
app = Flask(__name__)
BOOKS = [
    {"id": "abc-1234", "title": "ABC"},
    {"id": "def-5678", "title": "DEF"},
]
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    for book in BOOKS:
        if book["id"] == book_id:
            return jsonify(book), 200

    return jsonify({"error": "book not found"}), 404
@app.route("/books", methods=["GET"])
def get_books():
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    q = request.args.get("q", "").lower()
    items = [
        book for book in BOOKS
        if q in book["title"].lower()
    ]
    items = items[offset:offset + limit]
    return jsonify({"items": items}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)