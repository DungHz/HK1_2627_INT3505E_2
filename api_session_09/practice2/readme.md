# Practice 2 / 5 — Header Versioning với decorator `@api_version`

## Mục tiêu

Cùng một URL `GET /users/{id}` phục vụ nhiều phiên bản API. Client chọn
version qua header `X-API-Version`; server trả header `X-API-Version-Served`
để debug và đo adoption theo version.

| Header gửi lên              | Version phục vụ | Shape response                              |
|-----------------------------|-----------------|---------------------------------------------|
| *(không gửi)*               | `2` (LATEST)    | `id, first_name, last_name, email`          |
| `X-API-Version: 1`          | `1`             | `id, full_name`                             |
| `X-API-Version: 2`          | `2`             | `id, first_name, last_name, email`          |
| `X-API-Version: 2024-06-20` | `2024-06-20`    | giống v2 (date-based, kiểu Stripe-Version)  |
| `X-API-Version: 99`         | —               | **400** `unsupported version`               |

## Yêu cầu

- Python 3.9 trở lên
- pip

## Cài đặt

```bash
cd practice2
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Chạy server

```bash
python app.py
```

Server chạy ở `http://localhost:5000`.

## Test bằng curl

Mở terminal thứ hai. Cờ `-i` để xem cả response header.

> Windows PowerShell: dùng `curl.exe` thay cho `curl` (vì `curl` là alias
> của `Invoke-WebRequest`).

**1. Không gửi header → newest stable (v2)**
```bash
curl -i http://localhost:5000/users/1
```
```
HTTP/1.1 200 OK
X-API-Version-Served: 2
Vary: X-API-Version

{"email":"a@vnu.vn","first_name":"Văn","id":1,"last_name":"Nguyễn"}
```

**2. Chọn v1 tường minh**
```bash
curl -i -H "X-API-Version: 1" http://localhost:5000/users/1
```
```
HTTP/1.1 200 OK
X-API-Version-Served: 1

{"full_name":"Văn Nguyễn","id":1}
```

**3. Version dạng ngày**
```bash
curl -i -H "X-API-Version: 2024-06-20" http://localhost:5000/users/1
```
→ `200`, `X-API-Version-Served: 2024-06-20`, body theo schema v2.

**4. Version không hỗ trợ → 400**
```bash
curl -i -H "X-API-Version: 99" http://localhost:5000/users/1
```
```
HTTP/1.1 400 BAD REQUEST

{"error":"unsupported version","requested":"99","supported":["1","2","2024-06-20"]}
```

**5. User không tồn tại → 404**
```bash
curl -i -H "X-API-Version: 1" http://localhost:5000/users/999
```
→ `404`, body `{"error":"not found"}`.

## Chạy unit test

```bash
pytest -v
```
Kết quả mong đợi: 7 test đều `PASSED`.

## Giải thích nội dung — 4 điểm cần nhớ

1. **Decorator parse `X-API-Version`, thiếu thì dùng default.**
   `request.headers.get("X-API-Version") or default` — client không gửi
   header (hoặc gửi rỗng) sẽ nhận `LATEST = "2"`. Đây là ưu điểm của header
   versioning: URL chỉ đại diện cho resource, version tách riêng.

2. **Trả `X-API-Version-Served`.**
   Client và đội ops biết chính xác server đã phục vụ version nào. Log header
   này từ ngày đầu là cách đo adoption (bao nhiêu % traffic còn ở v1) trước
   khi lên kế hoạch deprecation.

3. **Handler trả shape khác nhau theo version.**
   Decorator truyền `version` vào tham số đầu tiên; handler rẽ nhánh
   `if version == "1"`. v1 trả `full_name`, v2 tách `first_name` +
   `last_name` — đây là **breaking change** (đổi tên field), nên bắt buộc
   phải có version mới.

4. **Version lạ → 400, không fallback.**
   Nếu âm thầm trả version mặc định, client gõ sai (`X-API-Version: 3`) sẽ
   nhận một shape không mong đợi mà không hề biết. Trả 400 kèm danh sách
   version hợp lệ giúp lỗi lộ ra ngay.

## Cải tiến so với code trên slide

| Vấn đề trong code slide | Đã sửa |
|---|---|
| User không tồn tại trả `{"error": ...}` với status **200** | Handler trả `(body, 404)`; decorator tách `body, status` |
| Không có `Vary` header — CDN có thể cache nhầm response v1 cho client v2 | Thêm `Vary: X-API-Version` |
| Header rỗng `X-API-Version: ` bị coi là version lạ | Header rỗng → dùng default |
| Tiếng Việt bị escape thành `\u0103...` | `app.json.ensure_ascii = False` |
| Lỗi 400 không nói version nào hợp lệ | Body trả thêm `requested` và `supported` |

## Hạn chế của header versioning (liên hệ lý thuyết)

- Mở URL trực tiếp trên trình duyệt không gửi được custom header → luôn nhận
  default; phải dùng `fetch`, Postman hoặc curl.
- Cache/CDN phải cấu hình `Vary` đúng, nếu không sẽ serve nhầm version.
- Dashboard/log quên ghi header thì đo sai traffic theo version.

## Bài tập mở rộng

1. Thêm version `3` với field mới `avatar_url` (thay đổi additive) — kiểm tra
   client v2 vẫn chạy bình thường.
2. Hỗ trợ thêm media-type versioning: đọc
   `Accept: application/vnd.acme.user.v2+json` nếu không có `X-API-Version`.
3. Kết hợp với Practice 3: khi `version == "1"`, gắn `Sunset` và
   `Deprecation: true` vào response.
4. Ghi log mỗi request theo dạng `version=<v> path=<path>` rồi đếm tỉ lệ
   traffic từng version.