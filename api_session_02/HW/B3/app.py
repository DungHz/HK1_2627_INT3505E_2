import hashlib
from flask import Flask, jsonify, request, make_response

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "Python", "author": "Nguyen Van An", "price": 25.99},
    {"id": 2, "title": "Flask", "author": "Tran Van Binh", "price": 32.50},
    {"id": 3, "title": "REST API", "author": "Le Minh Duc", "price": 28.00}
]
@app.get("/books/<int:bid>")
def get_book_with_etag(bid):
    book = next((b for b in BOOKS if b["id"] == bid), None)
    if book is None:
        return jsonify(error="not found"), 404
    book_string = str(book).encode('utf-8')
    etag = f'"{hashlib.md5(book_string).hexdigest()}"'
    client_etag = request.headers.get("If-None-Match")
    if client_etag == etag:
        return "", 304
    resp = make_response(jsonify(book), 200)
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=60" 
    return resp
if __name__ == '__main__':
    app.run(debug=True)