from flask import jsonify, request

def bad_request(message):
    return jsonify({
        "error": "bad_request",
        "message": message,
        "path": request.path
    }), 400
