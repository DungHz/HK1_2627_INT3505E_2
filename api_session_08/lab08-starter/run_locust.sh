#!/usr/bin/env bash
# Lab 4: chạy 3 kịch bản A/B/C, mỗi kịch bản trên DB sạch và server mới.
set -uo pipefail
cd "$(dirname "$0")"
mkdir -p reports instance

if curl -fsS http://127.0.0.1:5000/health > /dev/null 2>&1; then
  echo "Port 5000 đang có server chạy. Hãy dừng nó (Ctrl+C ở Terminal 1) rồi chạy lại."
  exit 1
fi

run_scenario() {
  local name=$1 users=$2 rate=$3 duration=$4
  echo "=== Kịch bản $name: $users users, spawn $rate/s, $duration ==="
  rm -f instance/books.db
  python -m app --port 5000 > "reports/server_$name.log" 2>&1 &
  local pid=$!

  for _ in $(seq 1 40); do
    curl -fsS http://127.0.0.1:5000/health > /dev/null 2>&1 && break
    sleep 0.25
  done

  locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
    -u "$users" -r "$rate" -t "$duration" \
    --html "reports/$name.html" --csv "reports/$name" --only-summary \
    2>&1 | tee "reports/locust_$name.log"

  kill "$pid" 2>/dev/null
  wait "$pid" 2>/dev/null
  sleep 1
}

run_scenario A 10 2 30s
run_scenario B 50 5 60s
run_scenario C 200 50 30s

python performance/summarize.py
