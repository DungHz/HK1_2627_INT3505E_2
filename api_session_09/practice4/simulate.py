"""
Mô phỏng phân bổ traffic theo hash bucket, không cần chạy server.

  python simulate.py                  # bảng phân bổ cho 10.000 account
  python simulate.py acct_7 acct_123  # xem bucket của từng account
"""
import sys

from gateway import bucket


def distribution(n=10_000, percents=(0, 5, 25, 50, 100)):
    accounts = [f"acct_{i}" for i in range(n)]
    buckets = {a: bucket(a) for a in accounts}

    print(f"{'V2_PERCENT':>10} | {'-> v2':>6} | {'-> v1':>6} | tỉ lệ v2")
    print("-" * 42)
    for p in percents:
        v2 = sum(b < p for b in buckets.values())
        print(f"{p:>10} | {v2:>6} | {n - v2:>6} | {v2 / n:.1%}")

    at_5 = {a for a, b in buckets.items() if b < 5}
    at_25 = {a for a, b in buckets.items() if b < 25}
    print(f"\nMọi account ở v2 khi 5% vẫn ở v2 khi 25%? {at_5 <= at_25}")


def show_accounts(accounts):
    for a in accounts:
        b = bucket(a)
        print(f"{a:<15} bucket={b:>2}  -> sang v2 khi V2_PERCENT > {b}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        show_accounts(sys.argv[1:])
    else:
        distribution()