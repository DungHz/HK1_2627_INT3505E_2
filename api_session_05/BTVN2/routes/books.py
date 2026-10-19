import base64
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import select, func, tuple_

from models import db, Book


bp = Blueprint(
    "books",
    __name__,
    url_prefix="/api/v1/books"
)


DEFAULT_LIMIT = 20
MAX_LIMIT = 100

SORT_FIELDS = {
    "id": Book.id,
    "title": Book.title,
    "price": Book.price_vnd,
    "genre": Book.genre
}


def parse_sort(raw):
    parts = raw.split(",")

    if not parts:
        return None

    result = []

    for part in parts:
        part = part.strip()

        if not part:
            return None

        desc = part.startswith("-")
        key = part.lstrip("-")

        if key not in SORT_FIELDS:
            return None

        column = SORT_FIELDS[key]

        result.append({
            "key": key,
            "column": column,
            "desc": desc
        })

    # Add id as tie-breaker if it is not already present
    if not any(item["key"] == "id" for item in result):
        result.append({
            "key": "id",
            "column": Book.id,
            "desc": result[-1]["desc"]
        })

    return result


def apply_sort(query, sort_fields):
    order_columns = []

    for item in sort_fields:
        column = item["column"]

        if item["desc"]:
            order_columns.append(column.desc())
        else:
            order_columns.append(column.asc())

    return query.order_by(*order_columns)


def encode_cursor(book, sort_fields, raw_sort):
    values = []

    for item in sort_fields:
        values.append(
            getattr(book, item["column"].key)
        )

    data = {
        "sort": raw_sort,
        "values": values
    }

    return base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).decode().rstrip("=")


def decode_cursor(raw):
    try:
        padding = "=" * (-len(raw) % 4)

        return json.loads(
            base64.urlsafe_b64decode(
                raw + padding
            ).decode()
        )

    except Exception:
        return None


def apply_cursor(query, cursor_data, sort_fields):
    values = cursor_data["values"]

    columns = [
        item["column"]
        for item in sort_fields
    ]

    # This implementation requires all cursor sort directions
    # to be the same.
    desc = sort_fields[0]["desc"]

    if any(
        item["desc"] != desc
        for item in sort_fields
    ):
        return None

    if desc:
        condition = tuple_(*columns) < tuple(values)
    else:
        condition = tuple_(*columns) > tuple(values)

    return query.where(condition)


@bp.get("")
def list_books():
    strategy = request.args.get(
        "strategy",
        "offset"
    )

    if strategy not in ("offset", "cursor"):
        return jsonify({
            "error": "strategy must be offset or cursor"
        }), 400

    limit = request.args.get(
        "limit",
        DEFAULT_LIMIT,
        type=int
    )

    if limit < 1:
        return jsonify({
            "error": "limit must be greater than 0"
        }), 400

    limit = min(limit, MAX_LIMIT)

    genre = request.args.get("genre")

    raw_sort = request.args.get(
        "sort",
        "id"
    )

    sort_fields = parse_sort(raw_sort)

    if sort_fields is None:
        return jsonify({
            "error": "invalid sort"
        }), 400

    query = select(Book)

    # Filter by genre
    if genre:
        query = query.where(
            Book.genre == genre
        )

    query = apply_sort(
        query,
        sort_fields
    )

    # OFFSET PAGINATION
    if strategy == "offset":
        offset = request.args.get(
            "offset",
            0,
            type=int
        )

        if offset < 0:
            return jsonify({
                "error": "offset must be >= 0"
            }), 400

        count_query = select(
            func.count(Book.id)
        )

        if genre:
            count_query = count_query.where(
                Book.genre == genre
            )

        total = db.session.scalar(
            count_query
        )

        rows = db.session.scalars(
            query
            .offset(offset)
            .limit(limit)
        ).all()

        return jsonify({
            "data": [
                book.to_dict()
                for book in rows
            ],
            "page": {
                "strategy": "offset",
                "offset": offset,
                "limit": limit,
                "total": total
            }
        }), 200

    # CURSOR PAGINATION
    raw_cursor = request.args.get(
        "cursor"
    )

    if raw_cursor:
        cursor_data = decode_cursor(
            raw_cursor
        )

        if cursor_data is None:
            return jsonify({
                "error": "invalid cursor"
            }), 400

        if cursor_data.get("sort") != raw_sort:
            return jsonify({
                "error": "cursor sort does not match request sort"
            }), 400

        if len(cursor_data.get("values", [])) != len(sort_fields):
            return jsonify({
                "error": "invalid cursor"
            }), 400

        query = apply_cursor(
            query,
            cursor_data,
            sort_fields
        )

        if query is None:
            return jsonify({
                "error": "cursor pagination requires sort fields with the same direction"
            }), 400

    rows = db.session.scalars(
        query.limit(limit + 1)
    ).all()

    more = len(rows) > limit

    items = rows[:limit]

    next_cursor = None

    if more and items:
        next_cursor = encode_cursor(
            items[-1],
            sort_fields,
            raw_sort
        )

    return jsonify({
        "data": [
            book.to_dict()
            for book in items
        ],
        "page": {
            "strategy": "cursor",
            "limit": limit,
            "next": next_cursor,
            "more": more
        }
    }), 200