# Practice 3 / 5 — Sunset middleware: decorator `@deprecate_at`

## Mục tiêu

Viết decorator `@deprecate_at(sunset_date)` tái sử dụng được cho mọi endpoint cũ:

| Thời điểm gọi        | Kết quả                                                              |
|----------------------|----------------------------------------------------------------------|
| Trước ngày sunset    | Response bình thường + `Sunset`, `Deprecation`, `Link` header        |
| Từ ngày sunset trở đi | **410 Gone** + body chỉ dẫn sang endpoint thay thế                   |
| Mọi lần gọi           | Server ghi log `WARNING` để biết client nào vẫn còn dùng bản cũ      |

Trong app demo: `/api/v1/users/{id}` bị deprecate (sunset 31/12/2026),
`/api/v2/users/{id}` là bản thay thế.

## Cấu trúc

```
practice3/
├── sunset.py         # decorator @deprecate_at (tái sử dụng)
├── app.py            # app demo: v1 deprecated, v2 thay thế
├── test_app.py       # 9 unit test (pytest)
├── requirements.txt
└── README.md
```

## Yêu cầu

- Python 3.9 trở lên
- Windows 10/11 (có sẵn `curl.exe`) hoặc macOS / Linux

## Cài đặt

**Windows (PowerShell)**
```powershell
cd practice3
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**
```bash
cd practice3
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Chạy server

```powershell
python app.py
```

Server chạy ở `http://localhost:5000` và in ra ngày sunset đang dùng.
Mở **terminal thứ hai** để test.

## Test bằng curl

> ⚠️ **Windows PowerShell:** gõ **`curl.exe`**, KHÔNG gõ `curl`
> (`curl` là alias của `Invoke-WebRequest`, sẽ báo lỗi *Cannot find drive 'http'*).
> macOS / Linux: dùng `curl` bình thường.

> 💡 Tiếng Việt hiện lỗi font trong PowerShell thì chạy trước:
> `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`

### 1. Trước sunset → 200 kèm header cảnh báo

```powershell
curl.exe -i http://localhost:5000/api/v1/users/1
```
```
HTTP/1.1 200 OK
Content-Type: application/json
Sunset: Thu, 31 Dec 2026 23:59:59 GMT
Deprecation: true
Link: </api/v2/users/1>; rel="successor-version"

{"full_name":"Văn Nguyễn","id":1}
```

Ở terminal chạy server sẽ thấy:
```
... WARNING [sunset] deprecated_call path=/api/v1/users/1 client=127.0.0.1 sunset=Thu, 31 Dec 2026 23:59:59 GMT
```

### 2. Endpoint thay thế v2 → không có header deprecation

```powershell
curl.exe -i http://localhost:5000/api/v2/users/1
```
→ `200`, body `{"email":"a@vnu.vn","first_name":"Văn","id":1,"last_name":"Nguyễn"}`,
không có `Sunset` / `Deprecation`.

### 3. User không tồn tại trên v1 → 404, vẫn có header cảnh báo

```powershell
curl.exe -i http://localhost:5000/api/v1/users/999
```

### 4. Sau sunset → 410 Gone

Không cần chờ đến 31/12/2026: đặt ngày sunset về quá khứ bằng biến môi trường
`V1_SUNSET`. Dừng server (Ctrl+C) rồi chạy lại:

**Windows (PowerShell)**
```powershell
$env:V1_SUNSET = "2020-01-01T00:00:00+00:00"
python app.py
```

**macOS / Linux**
```bash
V1_SUNSET=2020-01-01T00:00:00+00:00 python app.py
```

Gọi lại ở terminal thứ hai:
```powershell
curl.exe -i http://localhost:5000/api/v1/users/1
```
```
HTTP/1.1 410 GONE
Sunset: Wed, 01 Jan 2020 00:00:00 GMT
Deprecation: true
Link: </api/v2/users/1>; rel="successor-version"

{"error":"gone","sunset":"Wed, 01 Jan 2020 00:00:00 GMT","use_instead":"/api/v2/users/1"}
```

Log server đổi thành `gone_call ...`.

Xong thì xoá biến môi trường để quay về ngày sunset mặc định:
```powershell
Remove-Item Env:V1_SUNSET
```

## Chạy unit test

```powershell
pytest -v
```

Kết quả mong đợi: 9 test `PASSED`. Không cần bật server. Test dùng
`monkeypatch` thay hàm `sunset._now()` để giả lập thời gian trước, đúng
và sau ngày sunset — không phụ thuộc ngày thật trên máy.

## Giải thích nội dung

1. **`Sunset` header (RFC 8594)** — cho client biết *chính xác khi nào*
   endpoint ngừng chạy, theo định dạng HTTP-date (luôn ở múi giờ GMT).
   Hàm `http_date()` dùng `email.utils.format_datetime(..., usegmt=True)`
   để sinh đúng định dạng này.

2. **`Deprecation` header** — tín hiệu ngắn gọn để SDK / fetch wrapper /
   monitoring phát hiện "endpoint này đã bị deprecate" mà không cần parse
   chuỗi.

3. **`Link: <...>; rel="successor-version"`** — chỉ thẳng tới endpoint
   thay thế. `replacement="/api/v2/users/{uid}"` được điền tham số route,
   nên client nhận đúng URL của *chính resource đó* ở v2.

4. **410 Gone thay vì 404** — 404 nghĩa là "không tìm thấy" (có thể do gõ
   sai), còn 410 khẳng định "từng tồn tại, đã bị gỡ có chủ đích". Sau sunset
   handler cũ không được gọi nữa.

5. **Log mỗi lần gọi** — `deprecated_call` / `gone_call` kèm path và IP là
   dữ liệu để biết còn bao nhiêu client ở v1, ai cần được liên hệ trước khi
   tắt hẳn.

6. **So sánh thời gian luôn ở UTC** — decorator từ chối datetime không có
   timezone, tránh lỗi lệch 7 tiếng giữa giờ Việt Nam và GMT.

## Cải tiến so với code trên slide

| Vấn đề trong code slide | Đã sửa |
|---|---|
| Response 410 không có `Sunset`, `Link` header | 410 vẫn gắn đủ header |
| `jsonify(body)` lỗi nếu handler trả về `Response` | Dùng `make_response()`, chấp nhận dict, tuple hoặc Response |
| `Link` trỏ chung chung tới `/api/v2/users` | Hỗ trợ template `{uid}` → trỏ đúng resource |
| Không log các lần gọi sau sunset | Log `gone_call` |
| datetime không timezone gây `TypeError` lúc chạy | Báo `ValueError` rõ ràng ngay khi khai báo decorator |
| Không test được trường hợp sau sunset | Tách `_now()` để giả lập thời gian; thêm `V1_SUNSET` cho demo |
| Thiếu cấu hình logging nên log hiển thị khó đọc | `logging.basicConfig` có thời gian, level, tên logger |

### Ghi chú về chuẩn

- RFC 8594 (Sunset) đã là RFC chính thức (Informational, 05/2019), không còn
  là draft.
- Bản chính thức RFC 9745 (03/2025) quy định `Deprecation` là một **ngày**
  dạng `@<unix-timestamp>`, ví dụ `Deprecation: @1782864000` (= 01/07/2026).
  Giá trị `true` như trên slide đến từ các bản draft cũ. Decorator mặc định
  vẫn trả `true` để khớp bài học; truyền `deprecated_since=` để dùng định
  dạng chuẩn:
  ```python
  @deprecate_at(V1_SUNSET,
                replacement="/api/v2/users/{uid}",
                deprecated_since=datetime(2026, 7, 1, tzinfo=timezone.utc))
  ```

## Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Cannot find drive. A drive with the name 'http' does not exist` | Gõ `curl` trong PowerShell | Gõ `curl.exe` |
| Vẫn nhận 410 sau khi demo xong | Biến `V1_SUNSET` còn trong phiên PowerShell | `Remove-Item Env:V1_SUNSET` rồi chạy lại server |
| `ValueError: Invalid isoformat string` khi đặt `V1_SUNSET` | Python < 3.11 không hiểu hậu tố `Z` | Dùng `+00:00`, vd `2020-01-01T00:00:00+00:00` |
| Thấy mỗi dòng log in 2 lần lúc khởi động | Chế độ `debug=True` của Flask chạy reloader | Bình thường, không ảnh hưởng |
| `ModuleNotFoundError: No module named 'flask'` | Chưa kích hoạt venv | `.venv\Scripts\Activate.ps1` rồi `pip install -r requirements.txt` |

## Bài tập mở rộng

1. Kết hợp Practice 2: khi client gửi `X-API-Version: 1` thì gắn header
   sunset cho version 1 (thay vì cho cả một URL).
2. Thêm tham số `docs_url` → gắn thêm
   `Link: <docs_url>; rel="deprecation"` trỏ tới trang migration guide.
3. Đếm số lần `deprecated_call` theo từng client IP và thêm endpoint
   `/admin/deprecation-report` trả về thống kê.
4. Thêm "pha Restrict": trong 30 ngày cuối trước sunset, trả `429` ngẫu
   nhiên cho 50% request vào v1 để thúc client migrate.