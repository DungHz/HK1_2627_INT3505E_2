"""
Practice 4 / 5 — Routing 3 tầng: chọn handler v1 hoặc v2 cho cùng một URL.

Thứ tự ưu tiên:
  0. Kill switch (enabled = False)  -> 100% v1, dùng để rollback trong vài giây
  1. Header X-Cohort thuộc V2_COHORTS -> v2
  2. account_id thuộc allow-list      -> v2
  3. Hash bucket(account_id) < V2_PERCENT -> v2, còn lại v1
"""
import hashlib
import logging
import os

from flask import request

from handlers import v1_create_order, v2_create_order

log = logging.getLogger("gateway")

# Cấu hình rollout — có thể đổi lúc đang chạy qua /admin/rollout
CONFIG = {
    "enabled": True,                                  # kill switch
    "v2_percent": int(os.environ.get("V2_PERCENT", "5")),
    "v2_cohorts": {"beta", "internal"},
    "v2_force_accounts": {"acct_42", "acct_99"},
}


def bucket(account_id):
    """
    Map account_id vào bucket 0..99, luôn cố định cho cùng một account.
    Dùng md5 (không phải hash() của Python vì hash() đổi giá trị mỗi lần
    khởi động process). md5 ở đây chỉ để chia đều, không dùng cho bảo mật.
    """
    return int(hashlib.md5(account_id.encode("utf-8")).hexdigest(), 16) % 100


def route_to_v2(account_id, cohort=""):
    """Hàm thuần (không đọc request) để dễ test. Trả về (dùng_v2, lý_do)."""
    if not CONFIG["enabled"]:
        return False, "kill_switch"

    # 1. Cohort tường minh có ưu tiên cao nhất
    if cohort in CONFIG["v2_cohorts"]:
        return True, f"cohort:{cohort}"

    # 2. Account nằm trong allow-list
    if account_id in CONFIG["v2_force_accounts"]:
        return True, f"allowlist:{account_id}"

    # 3. Chia theo phần trăm, deterministic
    pct = CONFIG["v2_percent"]
    b = bucket(account_id)
    if b < pct:
        return True, f"bucket:{b}<{pct}"
    return False, f"bucket:{b}>={pct}"


def dispatch(body):
    cohort = request.headers.get("X-Cohort", "").strip().lower()
    account_id = body["account_id"]

    use_v2, reason = route_to_v2(account_id, cohort)
    which = "v2" if use_v2 else "v1"
    log.info("route account=%s cohort=%s -> %s (%s)",
             account_id, cohort or "-", which, reason)

    handler = v2_create_order if use_v2 else v1_create_order
    return which, reason, handler(body)


def config_snapshot():
    return {
        "enabled": CONFIG["enabled"],
        "v2_percent": CONFIG["v2_percent"],
        "v2_cohorts": sorted(CONFIG["v2_cohorts"]),
        "v2_force_accounts": sorted(CONFIG["v2_force_accounts"]),
    }