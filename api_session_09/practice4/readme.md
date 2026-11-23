# Practice 4 / 5 — Blue-Green routing: 1 URL, chọn v1 hoặc v2 theo cohort

> Hướng dẫn này dùng **Git Bash** trên Windows (cũng chạy y hệt trên
> macOS / Linux, chỉ khác lệnh kích hoạt venv).

## Mục tiêu

Cùng một URL `POST /orders`, gateway quyết định request đi vào
`v1_create_order` hay `v2_create_order` theo thứ tự ưu tiên:

| Ưu tiên | Điều kiện                                              | Kết quả | `X-Route-Reason`    |
|--------:|--------------------------------------------------------|---------|---------------------|
| 0       | Kill switch đang bật (`enabled = false`)               | v1      | `kill_switch`       |
| 1       | Header `X-Cohort: beta` hoặc `internal`                | v2      | `cohort:beta`       |
| 2       | `account_id` thuộc allow-list (`acct_42`, `acct_99`)   | v2      | `allowlist:acct_42` |
| 3       | `bucket(account_id) < V2_PERCENT`                      | v2      | `bucket:3<5`        |
| —       | Còn lại                                                | v1      | `bucket:37>=5`      |

Lộ trình rollout: 0% → beta → 5% → 25% → 100% → sunset v1.

Khác biệt v1 / v2 (breaking change có chủ đích):

|             | v1 (legacy)            | v2                          |
|-------------|------------------------|-----------------------------|
| Status code | `200 OK`               | `201 Created`               |
| ID đơn      | `order_id: "V1-00001"` | `id: "ord_00001"`           |
| Tiền        | `total: 150000`        | `amount: {value, currency}` |
| Trạng thái  | `created`              | `pending` + `created_at`    |

## Cấu trúc

```
practice4/
├── gateway.py        # logic routing 3 tầng + kill switch
├── handlers.py       # v1_create_order, v2_create_order
├── app.py            # POST /orders + /admin/rollout
├── simulate.py       # mô phỏng phân bổ % không cần server
├── test_app.py       # 15 unit test (pytest)
├── samples/          # (tuỳ chọn) body JSON mẫu
├── requirements.txt
└── README.md
```

## Yêu cầu

- Python 3.9 trở lên
- Git for Windows (đã kèm Git Bash và `curl`)

## Cài đặt

```bash
cd /d/INT3505E_2/api_session_09/practice4   # đổi theo đường dẫn của bạn
python -m venv .venv
source .venv/Scripts/activate               # macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Bật UTF-8 cho Python để in tiếng Việt không bị lỗi `UnicodeEncodeError`
trong Git Bash:

```bash
export PYTHONUTF8=1
```

Muốn khỏi gõ lại mỗi lần mở terminal:
`echo 'export PYTHONUTF8=1' >> ~/.bashrc`

> Ghi chú Git Bash:
> - Gõ `python`, không gõ `python3` (trên Windows `python3` thường là lối tắt
>   mở Microsoft Store).
> - Ổ `D:\` trong Git Bash là `/d/`.

## Chạy server

```bash
python app.py
```

Mặc định `V2_PERCENT = 5`. Khởi động với giá trị khác (biến chỉ áp dụng cho
đúng lệnh đó, không cần xoá sau):

```bash
V2_PERCENT=25 python app.py
```

Dòng đầu in ra: `Rollout ban đầu: {'enabled': True, 'v2_percent': 25, ...}`.

Mở **cửa sổ Git Bash thứ hai** để test. Dừng server bằng `Ctrl+C`.

## Test bằng curl

Cờ `-i` để xem cả response header. Luôn kèm
`-H "Content-Type: application/json"`, thiếu header này Flask không đọc body
là JSON và app trả 400.

### Case 1 — Cohort beta → v2

```bash
curl -i -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -H "X-Cohort: beta" \
  -d '{"account_id": "any", "amount": 150000}'
```
```
HTTP/1.1 201 CREATED
Content-Type: application/json
X-Order-Handler: v2
X-Route-Reason: cohort:beta

{
  "account_id": "any",
  "amount": {
    "currency": "VND",
    "value": 150000
  },
  "created_at": "2026-11-23T13:50:00+00:00",
  "id": "ord_00001",
  "status": "pending"
}
```

### Case 2 — Account trong allow-list → v2

```bash
curl -i -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"account_id": "acct_42", "amount": 250000}'
```
→ `201`, `X-Order-Handler: v2`, `X-Route-Reason: allowlist:acct_42`.

### Case 3 — Account thường, 5% → bucket quyết định

```bash
curl -i -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"account_id": "acct_7", "amount": 99000}'
```

Header `X-Route-Reason` cho biết bucket, ví dụ `bucket:61>=5` nghĩa là
`acct_7` ở bucket 61, chưa tới lượt sang v2. Nếu là v1, body có dạng:

```
{
  "account_id": "acct_7",
  "order_id": "V1-00001",
  "status": "created",
  "total": 99000
}
```

**Kiểm tra tính sticky** — gọi 5 lần, chỉ in header routing:

```bash
for i in 1 2 3 4 5; do
  curl -s -o /dev/null -D - -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d '{"account_id": "acct_7"}' | grep X-Route-Reason
done
```
Cả 5 dòng phải giống hệt nhau.

**Xem phân bổ trên server thật** — 20 account khác nhau:

```bash
for i in $(seq 0 19); do
  printf "acct_%-3s " "$i"
  curl -s -o /dev/null -D - -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d "{\"account_id\": \"acct_$i\"}" | grep -E "X-Order-Handler|X-Route-Reason" | tr -d '\r' | tr '\n' ' '
  echo
done
```

Biết trước bucket của một account mà không cần server:

```bash
python simulate.py acct_7 acct_123 any
```

### Case 4 — Đổi rollout khi đang chạy (không restart)

```bash
# Xem cấu hình hiện tại
curl http://localhost:5000/admin/rollout

# Tăng lên 100% -> mọi account thường sang v2
curl -X POST "http://localhost:5000/admin/rollout?percent=100"
```
Gọi lại Case 3 → giờ là `201`, `X-Order-Handler: v2`.

### Case 5 — Rollback bằng kill switch

```bash
curl -X POST "http://localhost:5000/admin/rollout?enabled=false"
```
Gọi lại Case 1 và Case 2 → cả hai về `200`, `X-Order-Handler: v1`,
`X-Route-Reason: kill_switch`. Đây là "tắt v2 trong 30 giây" của migration plan.

Bật lại:
```bash
curl -X POST "http://localhost:5000/admin/rollout?enabled=true"
```

### Case 6 — Request sai → 400

```bash
# Thiếu account_id
curl -i -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" -d '{"amount": 1}'

# Quên Content-Type
curl -i -X POST http://localhost:5000/orders -d '{"account_id": "acct_7"}'
```

### Log ở cửa sổ server

```
... INFO [gateway] route account=acct_7 cohort=- -> v1 (bucket:61>=5)
... WARNING [admin] rollout changed: {'enabled': False, ...}
```

### (Tuỳ chọn) Gửi body từ file

```bash
mkdir -p samples
printf '%s' '{"account_id": "any", "amount": 150000}'     > samples/order_any.json
printf '%s' '{"account_id": "acct_42", "amount": 250000}' > samples/order_acct_42.json
printf '%s' '{"account_id": "acct_7", "amount": 99000}'   > samples/order_acct_7.json

curl -i -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" -H "X-Cohort: beta" \
  --data-binary @samples/order_any.json
```

## Mô phỏng phân bổ traffic

```bash
python simulate.py
```
In bảng số account sang v2 với `V2_PERCENT` = 0, 5, 25, 50, 100 trên 10.000
account giả. Tỉ lệ thực tế xấp xỉ phần trăm cấu hình, và dòng cuối xác nhận
account đã sang v2 ở 5% thì vẫn ở v2 khi tăng lên 25%.

## Chạy unit test

```bash
pytest -v
```
Kết quả mong đợi: 15 test `PASSED`. Không cần bật server.

## Giải thích nội dung

1. **Một URL, nhiều implementation.** Client không phải đổi gì. Quyết định
   nằm ở gateway nên có thể đổi tỉ lệ, rollback mà không deploy lại client.

2. **Thứ tự ưu tiên có lý do.** Kill switch đứng đầu để rollback luôn thắng.
   Cohort tường minh (`beta`, `internal`) cho đội nội bộ / khách tình nguyện
   thử trước. Allow-list cho khách cụ thể đã cam kết migrate. Cuối cùng mới
   chia theo %.

3. **Hash bucket deterministic.** `md5(account_id) % 100` cho mỗi account một
   bucket cố định 0..99:
   - *Sticky*: cùng account luôn vào cùng version, không bị "nhảy" v1 ↔ v2
     giữa các request (quan trọng với đơn hàng, thanh toán).
   - *Đơn điệu*: tăng % chỉ thêm account sang v2, không đẩy account nào về v1.
   - Không dùng `hash()` của Python vì giá trị đổi mỗi lần khởi động process.

4. **Header quan sát được.** `X-Order-Handler` và `X-Route-Reason` cho biết
   request đi đâu và vì sao — thiếu chúng thì debug rollout gần như mù.

5. **Blue-green hay canary?** Chia theo % là **canary rollout**; lật
   `percent` 0 ↔ 100 hoặc dùng kill switch là **blue-green switch**. Bài này
   kết hợp cả hai trên cùng một gateway.

## Cải tiến so với code trên slide

| Vấn đề trong code slide | Đã sửa |
|---|---|
| Import `handlers` nhưng không có file | Thêm `handlers.py` với 2 shape khác nhau |
| `curl -d '{...}'` thiếu `Content-Type: application/json` nên Flask không đọc body | Mọi lệnh curl đều kèm header |
| `request.get_json()` trả `None` → `body.get` lỗi 500 | `get_json(silent=True)` + validate, trả 400 |
| Thiếu `account_id` thì mọi request rơi vào cùng bucket của chuỗi rỗng | Bắt buộc `account_id` là string |
| `V2_PERCENT` hard-code, phải sửa code để rollout | Đọc từ env + đổi lúc chạy qua `/admin/rollout` |
| Không có cách rollback nhanh | Kill switch `enabled` |
| `log` khai báo nhưng không dùng | Log mỗi quyết định routing |
| `route_to_v2` đọc `request` trực tiếp, khó test | Tách thành hàm thuần `route_to_v2(account_id, cohort)` |

## Lưu ý khi đưa ra production

- `CONFIG` nằm trong bộ nhớ của **một** process. Chạy nhiều worker
  (gunicorn, nhiều pod) thì mỗi worker có bản riêng → phải lưu cấu hình ở
  nơi dùng chung (Redis, database, dịch vụ feature flag, hoặc config của
  API gateway như Kong / Envoy / Nginx).
- Cấu hình reset về mặc định khi restart server (kể cả khi Flask debug tự
  reload lúc bạn sửa code).
- `/admin/rollout` trong bài **không có xác thực** — chỉ dùng để demo.

## Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `ModuleNotFoundError: No module named 'handlers'` | Thiếu `handlers.py` hoặc lưu thành `handlers.py.txt` | `ls` kiểm tra tên file, `mv handlers.py.txt handlers.py` |
| `UnicodeEncodeError` khi chạy `python app.py` / `simulate.py` | Git Bash không dùng UTF-8 cho Python | `export PYTHONUTF8=1` |
| `bash: .venv/bin/activate: No such file` | venv trên Windows nằm ở `Scripts` | `source .venv/Scripts/activate` |
| `python3` mở Microsoft Store hoặc không chạy | Lối tắt của Windows | Dùng `python` |
| `400` "body phải là JSON object" | Thiếu `Content-Type`, hoặc JSON sai | Thêm header; với file mẫu, xem ký tự ẩn bằng `cat -A samples/order_any.json` |
| `curl: Failed to open samples/...` | Không đứng trong thư mục `practice4` | `cd` vào `practice4` |
| `Failed to connect to localhost port 5000` | Server chưa chạy | `python app.py` ở cửa sổ kia |
| Rollout tự quay về 5% | Server restart / debug reload | Gọi lại `/admin/rollout` hoặc chạy `V2_PERCENT=... python app.py` |

## Bài tập mở rộng

1. Kết hợp Practice 3: gắn `@deprecate_at` cho nhánh v1 để response v1 có
   `Sunset` header trong lúc rollout.
2. Thêm endpoint `/admin/stats` đếm số request vào v1 / v2 theo từng
   `X-Route-Reason` — đây là adoption report hàng tuần của migration plan.
3. Thêm "shadow mode": với account ở v1, gọi thêm v2 ở chế độ nền, so sánh
   kết quả và log khác biệt, nhưng chỉ trả kết quả v1 cho client.
4. Thêm/xoá account khỏi allow-list qua `/admin/rollout`.