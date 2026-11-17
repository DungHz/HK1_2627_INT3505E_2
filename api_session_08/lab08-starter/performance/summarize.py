"""Đọc reports/{A,B,C}_stats.csv và in bảng markdown cho analysis.md."""
import csv
from pathlib import Path

REPORTS = Path(__file__).resolve().parent.parent / "reports"
SCENARIOS = [("A", 10, 2, "30s"), ("B", 50, 5, "60s"), ("C", 200, 50, "30s")]


def read_rows(name):
    path = REPORTS / f"{name}_stats.csv"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fail_rate(row):
    total = int(row["Request Count"])
    return 100 * int(row["Failure Count"]) / total if total else 0.0


print("| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |")
print("|---|---:|---:|---:|---:|---:|---:|")
for name, users, rate, duration in SCENARIOS:
    rows = read_rows(name)
    if rows is None:
        print(f"| {name} | {users} | {rate} | {duration} | (chưa chạy) | | |")
        continue
    agg = next(r for r in rows if r["Name"] == "Aggregated")
    print(f"| {name} | {users} | {rate} | {duration} | {agg['95%']} | "
          f"{fail_rate(agg):.2f}% | {float(agg['Requests/s']):.1f} |")

for name, *_ in SCENARIOS:
    rows = read_rows(name)
    if rows is None:
        continue
    print(f"\n#### Kịch bản {name}, theo endpoint\n")
    print("| Endpoint | # reqs | # fails | Fail % | p50 | p95 | p99 | Max | RPS |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['Type']} {r['Name']} | {r['Request Count']} | {r['Failure Count']} | "
              f"{fail_rate(r):.2f}% | {r['50%']} | {r['95%']} | {r['99%']} | "
              f"{float(r['Max Response Time']):.0f} | {float(r['Requests/s']):.1f} |")

    failures = REPORTS / f"{name}_failures.csv"
    if failures.exists():
        with failures.open(encoding="utf-8") as f:
            items = list(csv.DictReader(f))
        if items:
            print(f"\nFailures ({name}):")
            for item in items:
                print(f"- {item['Method']} {item['Name']}: {item['Error']} x{item['Occurrences']}")
