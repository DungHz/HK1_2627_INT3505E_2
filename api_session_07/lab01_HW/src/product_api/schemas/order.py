"""Marshmallow schemas for Order and OrderItem."""

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from .product import ProductSummaryOut


class OrderItemIn(Schema):
    product_id = fields.Int(required=True, validate=validate.Range(min=1))
    quantity = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    items = fields.List(
        fields.Nested(OrderItemIn),
        required=True,
        validate=validate.Length(min=1, max=100),
    )

    @validates_schema
    def validate_unique_products(self, data, **kwargs):
        product_ids = [item["product_id"] for item in data.get("items", [])]
        if len(product_ids) != len(set(product_ids)):
            raise ValidationError({
                "items": ["A product may appear only once in an order; combine its quantity."]
            })


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    quantity = fields.Int()
    unit_price_cents = fields.Int()
    product = fields.Nested(ProductSummaryOut)


class OrderOut(Schema):
    id = fields.Int()
    status = fields.Str()
    created_at = fields.DateTime(format="iso")
    items = fields.Nested(OrderItemOut, many=True)


class OrderListOut(Schema):
    items = fields.Nested(OrderOut, many=True)
    page = fields.Int()
    size = fields.Int()
    total = fields.Int()
