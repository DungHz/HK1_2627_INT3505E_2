import base64
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import select, tuple_

from models import db, Book


bp = Blueprint(
    "books",
    __name__,
    url_prefix="/api/v1/books"
)


SORT = {
    "id": Book.id,
    "price": Book.price_vnd
}


def parse_sort(raw):
    desc = raw.startswith("-")
    key = raw.lstrip("-")

    if key not in SORT:
        return None, "bad_sort", 400

    p = SORT[key]

    cols = [
        p.desc() if desc else p.asc(),
        Book.id.desc() if desc else Book.id.asc()
    ]

    return p, cols, desc


def _enc(s):
    return base64.urlsafe_b64encode(
        json.dumps(s).encode()
    ).decode().rstrip("=")


def apply_cursor(q, raw, sort, p, desc):
    if not raw:
        return q, None, 200

    try:
        pad = "=" * (-len(raw) % 4)

        c = json.loads(
            base64.urlsafe_b64decode(raw + pad)
        )

        if c.get("s") != sort:
            return None, "sort_chg", 400

        v = c["v"]
        i = c["i"]

        op = "<" if desc else ">"

        condition = tuple_(p, Book.id).op(op)(
            (v, i)
        )

        return q.filter(condition), None, 200

    except Exception:
        return None, "bad_cursor", 400


def build_response(items, lim, sort, p, more):
    nxt = None

    if items and more:
        last = items[-1]

        nxt = _enc({
            "s": sort,
            "v": getattr(last, p.key),
            "i": last.id
        })

    return jsonify({
        "data": [
            book.to_dict()
            for book in items
        ],
        "page": {
            "next": nxt,
            "more": more
        }
    })


@bp.get("")
def list_books():
    raw = request.args.get("cursor")

    lim = min(
        request.args.get(
            "limit",
            20,
            type=int
        ),
        100
    )

    sort = request.args.get(
        "sort",
        "-id"
    )

    cat = request.args.get(
        "category",
        type=int
    )

    p, cols, desc = parse_sort(sort)

    if p is None:
        return {
            "error": cols
        }, 400

    q = select(Book).order_by(*cols)

    if cat:
        q = q.filter(
            Book.category_id == cat
        )

    q, err, code = apply_cursor(
        q,
        raw,
        sort,
        p,
        desc
    )

    if err:
        return {
            "error": err
        }, code

    rows = db.session.scalars(
        q.limit(lim + 1)
    ).all()

    return build_response(
        rows[:lim],
        lim,
        sort,
        p,
        len(rows) > lim
    )