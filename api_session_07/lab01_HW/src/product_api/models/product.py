"""Product persistence model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, false, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_in_stock: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Force API queries to opt into eager loading when order history is needed.
    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product", lazy="raise"
    )
