# Lab 3 — Chạy Postman collection bằng Newman

## Yêu cầu

- Python 3.9+ và các package trong `requirements.txt`
- Node.js 18+ (kiểm tra bằng `node -v`)
- Newman: `npm install -g newman` (hoặc dùng `npx --yes newman`, script tự xử lý)

## Cài đặt (chỉ làm một lần)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p instance
```

## Chạy

Terminal 1, khởi động API và để nguyên cửa sổ:

```bash
source .venv/bin/activate
python -m app --port 5000
```

Terminal 2, chạy collection:

```bash
./run_newman.sh
```

Lệnh tương đương nếu không dùng script:

```bash
newman run books-api.postman_collection.json \
  -e postman/local.postman_environment.json \
  -r cli,junit --reporter-junit-export reports/junit.xml
```

## Kết quả mong đợi

- 7 request, 16 assertion, 0 failed
- Báo cáo JUnit được ghi vào `reports/junit.xml`

## Nội dung collection

| Folder | Request | Kiểm tra |
|---|---|---|
| books | GET /books | 200, body là array |
| books | POST /books | 201, id > 0, lưu `book_id` vào collection variable |
| books | GET /books/{{book_id}} | 200, đủ 5 trường |
| books | PUT /books/{{book_id}} | 200, title đã đổi |
| books | DELETE /books/{{book_id}} | 204, body rỗng |
| error-cases | POST /books thiếu title | 400, code VALIDATION_ERROR, errors có field title |
| error-cases | GET /books/9999 | 404, code NOT_FOUND, Content-Type JSON |

## Lỗi thường gặp

- `unable to open database file`: chưa tạo thư mục, chạy `mkdir -p instance`.
- `API chưa chạy`: Terminal 1 chưa khởi động server.
- `newman: command not found`: cài Newman hoặc để script tự dùng `npx`.
