from flask import jsonify, request

ERROR_BASE = "https://api.example.com/problems"


class ApiProblem(Exception):
    def __init__(
        self,
        status,
        title,
        detail=None,
        type_path=None,
        **extra
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type = (
            f"{ERROR_BASE}/{type_path}"
            if type_path
            else "about:blank"
        )
        self.extra = extra


def _problem(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": (
            f"{ERROR_BASE}/{type_path}"
            if type_path
            else "about:blank"
        ),
        "title": title,
        "status": status,
        "instance": request.path
    }

    if detail:
        body["detail"] = detail

    body.update(extra)

    resp = jsonify(body)
    resp.status_code = status
    resp.headers["Content-Type"] = "application/problem+json"

    return resp