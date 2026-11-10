# Backend Service - BTVN Buoi 7

Project Flask hoan thien Lab 1 va 5 yeu cau bai tap ve nha trong slide Backend Service.

## 1. Chuc nang da lam

- Product CRUD: danh sach co phan trang, xem chi tiet, tao, reserve, PATCH va soft-delete.
- `Order` co nhieu `OrderItem`; moi `OrderItem` lien ket mot `Product` qua `product_id`.
- Moi dong OrderItem luu `quantity` va `unit_price_cents` tai thoi diem dat hang.
- Tao order se tru ton kho. Neu mot san pham khong du hang, toan bo giao dich rollback.
- Blueprint rieng cho `/api/v1/orders`.
- Application factory, SQLAlchemy 2.x, Marshmallow, Flask-Migrate/Alembic.
- Dockerfile multi-stage va Docker Compose voi PostgreSQL.
- Hai probe tach biet: `/healthz` (liveness, khong truy cap DB) va `/ready` (readiness, kiem tra DB).
- Pytest cho Product POST va Order POST; test GET Order dem so SELECT de phat hien N+1.

## 2. Cau truc thu muc

```text
backend_service_homework/
|-- src/product_api/
|   |-- api/                 # products, orders, health blueprints
|   |-- models/              # Product, Order, OrderItem
|   |-- schemas/             # Marshmallow input/output schemas
|   |-- config.py
|   |-- errors.py
|   |-- extensions.py
|   `-- factory.py
|-- migrations/              # Alembic migration co san
|-- tests/
|-- Dockerfile
|-- docker-compose.yml
|-- requirements.txt
`-- wsgi.py
```

## 3. Chay local tren Windows PowerShell

Can Python 3.10+ (Docker image dung Python 3.12).

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
$env:DB_URL = "sqlite:///dev.db"
flask --app "product_api.factory:create_app()" db upgrade
flask --app "product_api.factory:create_app()" run --debug
```

API chay tai `http://127.0.0.1:5000`. SQLite database duoc tao trong thu muc `instance/` cua Flask app.

## 4. Chay bang Docker Compose

Can cai Docker Engine/Desktop va Docker Compose plugin.

```bash
docker compose up --build -d
docker compose ps
docker compose logs -f api
```

Compose se:

1. Khoi dong PostgreSQL va doi den khi healthcheck thanh cong.
2. Chay `flask db upgrade` de ap dung migration.
3. Khoi dong Flask app bang Gunicorn.

API: `http://localhost:5000`. Dung bang `docker compose down`; muon xoa ca du lieu PostgreSQL thi dung `docker compose down -v`.

Thong tin PostgreSQL trong compose chi danh cho bai tap/local development. Khi deploy that, can doi password va secret bang bien moi truong rieng, khong commit secret len Git.

## 5. API endpoints

| Method | URL | Mo ta |
|---|---|---|
| GET | `/api/v1/products?page=1&size=20` | Danh sach Product, phan trang |
| GET | `/api/v1/products/{id}` | Chi tiet Product |
| POST | `/api/v1/products` | Tao Product; SKU trung tra 409 |
| POST | `/api/v1/products/{id}/reserve` | Tru ton kho; khong cho am ton |
| PATCH | `/api/v1/products/{id}` | Cap nhat mot phan |
| DELETE | `/api/v1/products/{id}` | Soft-delete (`archived=true`) |
| POST | `/api/v1/orders` | Tao Order gom nhieu OrderItem |
| GET | `/api/v1/orders?page=1&size=20` | Danh sach Order kem items va Product |
| GET | `/api/v1/orders/{id}` | Chi tiet Order kem items va Product |
| GET | `/healthz` | Liveness probe, khong goi DB |
| GET | `/ready` | Readiness probe, kiem tra DB |

### Tao Product

```json
{
  "sku": "KB-001",
  "name": "Keyboard",
  "description": "Mechanical keyboard",
  "price_cents": 125000,
  "qty_in_stock": 10
}
```

### Tao Order gom nhieu Product

```json
{
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 2, "quantity": 1}
  ]
}
```

Moi `product_id` chi xuat hien mot lan trong mot Order; neu muon dat nhieu don vi thi tang `quantity`. Gia ban tai thoi diem tao Order duoc luu trong `unit_price_cents`, khong bi thay doi khi gia Product duoc cap nhat sau nay.

Response loi co dang:

```json
{
  "code": "out_of_stock",
  "message": "Not enough stock for product 'KB-001'"
}
```

Validation loi tra HTTP 422; khong tim thay tra 404; xung dot ton kho/SKU tra 409.

## 6. Chay pytest

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

Linux/macOS:

```bash
PYTHONPATH=src python -m pytest -q
```

Test `test_get_order_uses_eager_loading_without_n_plus_one` tao Order co hai san pham, sau do dem SELECT khi GET chi tiet. Ky vong 2 SELECT:

1. Lay Order.
2. Lay OrderItem va JOIN Product bang `selectinload(Order.items).joinedload(OrderItem.product)`.

So truy van khong tang theo so OrderItem, tranh mau hinh 1 + N query.

## 7. Migration khi thay doi Model

Sau khi sua Model:

```bash
flask --app "product_api.factory:create_app()" db migrate -m "describe_change"
```

Doc va kiem tra file moi trong `migrations/versions/`, sua tay neu Alembic nhan dien sai viec doi ten cot/bang, sau do:

```bash
flask --app "product_api.factory:create_app()" db upgrade
```

Khong sua migration da ap dung tren moi truong dung chung; tao revision moi de thay doi schema.
