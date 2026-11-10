"""Product CRUD and inventory reservation endpoints."""

from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError

from ..errors import Conflict, NotFound, OutOfStock
from ..extensions import db
from ..models import Product
from ..schemas.product import PaginationQuery, ProductIn, ProductOut, ProductPatch, ReserveIn

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


def _active_product_or_404(product_id: int) -> Product:
    product = db.session.scalar(db.select(Product).where(
        Product.id == product_id,
        Product.archived.is_(False),
    ))
    if product is None:
        raise NotFound("Product not found")
    return product


@products_bp.get("")
def list_products():
    paging = PaginationQuery().load(request.args)
    page, size = paging["page"], paging["size"]
    active_filter = Product.archived.is_(False)

    rows = db.session.execute(
        db.select(Product)
        .where(active_filter)
        .order_by(Product.id)
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()
    total = db.session.scalar(
        db.select(func.count(Product.id)).where(active_filter)
    ) or 0

    return jsonify({
        "items": ProductOut(many=True).dump(rows),
        "page": page,
        "size": size,
        "total": total,
    }), 200


@products_bp.get("/<int:product_id>")
def get_product(product_id: int):
    product = _active_product_or_404(product_id)
    return jsonify(ProductOut().dump(product)), 200


@products_bp.post("")
def create_product():
    body = ProductIn().load(request.get_json())
    product = Product(**body)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise Conflict("A product with this SKU already exists") from error
    return jsonify(ProductOut().dump(product)), 201


@products_bp.post("/<int:product_id>/reserve")
def reserve_product(product_id: int):
    body = ReserveIn().load(request.get_json())
    qty = body["qty"]
    _active_product_or_404(product_id)

    # The conditional UPDATE makes the stock check and decrement atomic.
    result = db.session.execute(
        update(Product)
        .where(
            Product.id == product_id,
            Product.archived.is_(False),
            Product.qty_in_stock >= qty,
        )
        .values(qty_in_stock=Product.qty_in_stock - qty)
    )
    if result.rowcount != 1:
        db.session.rollback()
        raise OutOfStock("Not enough stock to reserve the requested quantity")

    db.session.commit()
    product = _active_product_or_404(product_id)
    return jsonify(ProductOut().dump(product)), 200


@products_bp.patch("/<int:product_id>")
def patch_product(product_id: int):
    body = ProductPatch().load(request.get_json(), partial=True)
    if not body:
        raise ValidationError({"_schema": ["PATCH body must contain at least one supported field."]})

    product = _active_product_or_404(product_id)
    for field_name, value in body.items():
        setattr(product, field_name, value)
    db.session.commit()
    return jsonify(ProductOut().dump(product)), 200


@products_bp.delete("/<int:product_id>")
def delete_product(product_id: int):
    product = _active_product_or_404(product_id)
    product.archived = True
    db.session.commit()
    return "", 204
