"""Hai implementation của 'tạo đơn hàng'. v2 đổi shape response (breaking)."""
from datetime import datetime, timezone
from itertools import count

_v1_ids = count(1)
_v2_ids = count(1)


def v1_create_order(body):
    # Shape cũ: tổng tiền là một số phẳng, không có currency
    return {
        "order_id": f"V1-{next(_v1_ids):05d}",
        "account_id": body["account_id"],
        "total": body.get("amount", 0),
        "status": "created",
    }


def v2_create_order(body):
    # Shape mới: đổi tên field, tiền thành object có currency, thêm created_at
    return {
        "id": f"ord_{next(_v2_ids):05d}",
        "account_id": body["account_id"],
        "amount": {
            "value": body.get("amount", 0),
            "currency": body.get("currency", "VND"),
        },
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }