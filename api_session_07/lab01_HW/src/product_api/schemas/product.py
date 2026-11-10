"""Marshmallow schemas for Product input and output."""

from marshmallow import Schema, fields, validate


class ProductOut(Schema):
    id = fields.Int(dump_only=True)
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()
    created_at = fields.DateTime(format="iso", dump_only=True)


class ProductSummaryOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    price_cents = fields.Int()


class ProductIn(Schema):
    sku = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32),
    )
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, load_default=None,
                             validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))


class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    price_cents = fields.Int(validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class PaginationQuery(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
