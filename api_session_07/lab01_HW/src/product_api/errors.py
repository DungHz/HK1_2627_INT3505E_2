"""Application exceptions and consistent JSON error responses."""

from flask import Flask, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class OutOfStock(Conflict):
    code = "out_of_stock"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return jsonify({"code": error.code, "message": error.message}), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return jsonify({
            "code": "validation_error",
            "message": "Request validation failed",
            "details": error.messages,
        }), 422

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        status = error.code or 500
        code = (error.name or "http_error").lower().replace(" ", "_")
        return jsonify({"code": code, "message": error.description}), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled application exception")
        return jsonify({
            "code": "internal_error",
            "message": "An unexpected server error occurred.",
        }), 500
