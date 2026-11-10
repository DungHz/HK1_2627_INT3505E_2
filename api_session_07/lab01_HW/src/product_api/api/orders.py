"""Order resource. Each order can contain multiple OrderItem rows."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func, update
from sqlalchemy.orm import joinedload, selectinload

from ..errors import NotFound, OutOfStock
from ..extensions import db
from ..models import Order, OrderItem, Product
from ..schemas.order import OrderIn, OrderOut
from ..schemas.product import PaginationQuery

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def _order_query():
    # Two SELECTs for a page of orders: orders, then order_items JOIN products.
    return db.select(Order).options(
        selectinload(Order.items).joinedload(OrderItem.product)
    )


def _order_or_404(order_id: int) -> Order:
    order = db.session.scalar(_order_query().where(Order.id == order_id))
    if order is None:
        raise NotFound("Order not found")
    return order


@orders_bp.post("")
def create_order():
    body = OrderIn().load(request.get_json())
    requested_items = body["items"]
    product_ids = [item["product_id"] for item in requested_items]

    products = db.session.execute(
        db.select(Product).where(
            Product.id.in_(product_ids),
            Product.archived.is_(False),
        )
    ).scalars().all()
    products_by_id = {product.id: product for product in products}

    missing_ids = [product_id for product_id in product_ids if product_id not in products_by_id]
    if missing_ids:
        raise NotFound(f"Product not found or archived: {missing_ids[0]}")

    try:
        # Check and decrement stock atomically for every item. Any failure rolls back all items.
        for item in requested_items:
            result = db.session.execute(
                update(Product)
                .where(
                    Product.id == item["product_id"],
                    Product.archived.is_(False),
                    Product.qty_in_stock >= item["quantity"],
                )
                .values(qty_in_stock=Product.qty_in_stock - item["quantity"])
            )
            if result.rowcount != 1:
                product = products_by_id[item["product_id"]]
                raise OutOfStock(f"Not enough stock for product '{product.sku}'")

        order = Order(status="pending")
        db.session.add(order)
        db.session.flush()  # Get order.id before inserting the item rows.

        for item in requested_items:
            product = products_by_id[item["product_id"]]
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item["quantity"],
                unit_price_cents=product.price_cents,
            ))

        order_id = order.id
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    # Reload with eager loading; serialization must not trigger lazy queries.
    order = _order_or_404(order_id)
    return jsonify(OrderOut().dump(order)), 201


@orders_bp.get("")
def list_orders():
    paging = PaginationQuery().load(request.args)
    page, size = paging["page"], paging["size"]

    rows = db.session.execute(
        _order_query()
        .order_by(Order.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).scalars().all()
    total = db.session.scalar(db.select(func.count(Order.id))) or 0

    return jsonify({
        "items": OrderOut(many=True).dump(rows),
        "page": page,
        "size": size,
        "total": total,
    }), 200


@orders_bp.get("/<int:order_id>")
def get_order(order_id: int):
    order = _order_or_404(order_id)
    return jsonify(OrderOut().dump(order)), 200
