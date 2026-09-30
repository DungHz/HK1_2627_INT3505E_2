from flask import Flask, jsonify, request

app = Flask(__name__)

POSTS = [
    {
        "id": 1,
        "title": "Hello REST API",
        "content": "Nội dung bài viết",
        "user_id": 1
    }
]

# GET /api/v1/posts
@app.route("/api/v1/posts", methods=["GET"])
def get_posts():
    return jsonify(POSTS), 200

# POST /api/v1/posts
@app.route("/api/v1/posts", methods=["POST"])
def create_post():
    data = request.get_json(silent=True) or {}
    if not data.get("title"):
        return jsonify({"error": "title is required"}), 400
    post = {
        "id": len(POSTS) + 1,
        "title": data["title"],
        "content": data.get("content", ""),
        "user_id": data.get("user_id")
    }
    POSTS.append(post)
    return jsonify(post), 201


if __name__ == "__main__":
    app.run(debug=True)