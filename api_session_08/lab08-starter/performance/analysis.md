# Lab 4 — Phân tích kết quả

Môi trường đo: macOS, Python 3.9.6, Locust 2.34.0, Flask development server
(threaded) + SQLite, Locust và server chạy chung một máy. Mỗi kịch bản chạy
trên database mới và server vừa khởi động lại (script `run_locust.sh`).
Locustfile: 4 task với trọng số 3:2:1:1 (GET /books, GET /books/{id},
POST /books, GET /books?year=), `wait_time = between(1, 3)`.

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 15 | 0.00% | 4.7 |
| B | 50 | 5 | 60s | 14 | 0.00% | 23.4 |
| C | 200 | 50 | 30s | 34 | 0.04% | 98.1 |

### p95 theo endpoint (ms)

| Endpoint | A | B | C |
|---|---:|---:|---:|
| GET /books | 14 | 13 | 40 |
| GET /books/{id} | 24 | 12 | 28 |
| GET /books?year={year} | 15 | 12 | 32 |
| POST /books | 15 | 17 | 34 |

Báo cáo đầy đủ: `reports/A.html`, `reports/B.html`, `reports/C.html`.

## 1. Kịch bản có p95 cao nhất

Kịch bản **C** có p95 cao nhất: 34 ms, so với 15 ms (A) và 14 ms (B). Mọi
endpoint đều tăng p95 ở C, mạnh nhất là GET /books (13 → 40 ms) và
POST /books (17 → 34 ms).

Giải thích dựa trên số liệu:

- RPS tăng gần tuyến tính theo số user (4.7 → 23.4 → 98.1, xấp xỉ users / 2).
  Đây là giới hạn do `wait_time` trung bình 2 giây, nghĩa là server **chưa
  bão hoà**: nếu server là nút thắt thì RPS ở C sẽ thấp hơn nhiều so với 100.
- Dù chưa bão hoà, ở C có 200 luồng client và nhiều request đến cùng lúc hơn,
  nên một phần request phải xếp hàng chờ CPU (Python GIL, luồng của Flask dev
  server, khoá ghi của SQLite). Điều này làm **đuôi phân phối** dài ra: p50
  của C vẫn chỉ 4 ms nhưng p95 lên 34 ms và p99 lên 58 ms.
- Spawn rate 50 user/giây khiến cả 200 user khởi động trong khoảng 4 giây,
  tạo một đợt dồn request ở đầu kịch bản.

Lưu ý: p50 của C (4 ms) thấp hơn A/B (8–9 ms). Tôi không đủ dữ liệu để khẳng
định nguyên nhân (có thể do CPU tăng xung nhịp khi tải cao, hoặc do cache);
điều này cho thấy độ trễ ở mức vài ms rất nhạy với nhiễu của máy đo. Ở kịch
bản A, p99 (36 ms) gần bằng max vì chỉ có 136 request: percentile cao trên mẫu
nhỏ không ổn định.

## 2. Endpoint nào tăng failure rate? Lỗi thật hay lỗi đánh dấu?

**Không có lỗi HTTP thật nào** ở cả 3 kịch bản: không có 4xx ngoài dự kiến,
không có 5xx, không có timeout hay connection error. Log server
(`reports/server_*.log`) không có response 500.

Failure duy nhất: **1 lần ở GET /books?year={year}, kịch bản C**, với thông
báo `SIMULATED client-side failure (server returned 200)`. Đây là failure
**giả lập phía client**: Locust gọi `response.failure()` với xác suất 1%
trong khi server vẫn trả HTTP 200. Nó không phản ánh lỗi của API.

Số failure giả lập thấp hơn kỳ vọng 1% (A: 0/22, B: 0/206, C: 1/372; kỳ vọng
khoảng 0.2 / 2 / 3.7). Với số mẫu nhỏ như vậy, chênh lệch này nằm trong dao
động ngẫu nhiên bình thường.

Kết luận: **không endpoint nào có failure rate thật tăng theo số user** ở mức
tải đã thử. Dựa trên code, nếu tăng tải đến mức bão hoà thì ứng viên lỗi đầu
tiên là **POST /books**: SQLite chỉ cho một transaction ghi tại một thời
điểm, nên khi nhiều request ghi đồng thời có thể gặp
`database is locked` → HTTP 500.

## 3. SLO giả định p95 < 300 ms

**Cả 3 kịch bản đều đạt**, với khoảng dư lớn (p95 lớn nhất 34 ms, p99 lớn
nhất 58 ms, max 89 ms).

Giới hạn của phép đo, không được dùng kết quả này để khẳng định SLO
production:

- Flask development server và SQLite không phải cấu hình production
  (production thường dùng gunicorn/uwsgi nhiều worker và Postgres/MySQL).
- Locust và server chạy chung máy, tranh CPU với nhau; mạng là loopback nên
  không có độ trễ mạng thật.
- Thời gian chạy chỉ 30–60 giây: không phát hiện được rò rỉ bộ nhớ, tăng
  kích thước DB lâu dài (cần soak test).
- `wait_time` 1–3 s giới hạn RPS ở khoảng users / 2; tải thực tế đạt tối đa
  khoảng 98 RPS nên **chưa tìm được điểm vỡ** của hệ thống.
- DB nhỏ (vài trăm bản ghi); GET /books luôn giới hạn 20 bản ghi/trang.
- Độ trễ đo ở phía Locust, không gồm thời gian render phía client thật.

Đề xuất baseline cho CI gate (chạy kịch bản B trên runner CI cố định):

- p95 tổng hợp < 100 ms (khoảng 7 lần mức đo được, chừa biên cho runner CI
  chậm hơn máy cá nhân);
- failure rate thật (không tính failure giả lập) = 0%, hoặc < 1% nếu có
  endpoint phụ thuộc bên ngoài;
- cảnh báo hồi quy nếu p95 tăng quá 50% so với lần chạy baseline trước đó,
  vì một ngưỡng tuyệt đối rộng sẽ không phát hiện được thoái hoá dần.

## 4. Nếu connection pool bị giới hạn ở 5

Với cấu hình hiện tại, theo định luật Little, số request đang xử lý trung
bình ở kịch bản C chỉ khoảng 98 RPS × 0.004 s ≈ 0.4. Vì vậy pool 5 kết nối
gần như **không bị dùng hết**, và chạy lại kịch bản C nguyên trạng nhiều khả
năng sẽ không thấy khác biệt. Muốn quan sát ảnh hưởng, phải tạo đủ đồng thời.

Cách kiểm chứng:

1. Giới hạn pool trong `create_app` qua config:
   `SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 5, "max_overflow": 0, "pool_timeout": 1}`.
2. Tăng mức đồng thời: đặt `wait_time = constant(0)` trong một locustfile
   riêng (hoặc làm chậm truy vấn có chủ đích), chạy 200 user.
3. Chạy hai lần với cùng locustfile: một lần pool mặc định (đối chứng),
   một lần pool 5, và so sánh.

Dấu hiệu cần quan sát nếu pool là nút thắt:

- Log server có `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5
  overflow 0 reached`, Locust ghi nhận HTTP 500 (lỗi thật, không phải giả lập).
- p95/p99 tăng vọt đến gần `pool_timeout` (khoảng 1000 ms) vì request phải
  chờ kết nối rảnh.
- RPS ngừng tăng dù tăng số user: throughput bị chặn bởi 5 kết nối.
