from flask.views import MethodView
from flask_smorest import Blueprint, abort

from .schemas import ProductSchema


blp = Blueprint(
    "products",
    "products",
    url_prefix="/api/products",
    description="API quản lý sản phẩm"
)

# Dữ liệu mẫu, thay database để dự án đơn giản
products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 15000000,
        "description": "Laptop dành cho sinh viên"
    },
    {
        "id": 2,
        "name": "Mouse",
        "price": 250000,
        "description": "Chuột không dây"
    }
]


@blp.route("/")
class ProductList(MethodView):

    # GET /api/products/
    @blp.response(200, ProductSchema(many=True))
    def get(self):
        """Lấy danh sách sản phẩm"""
        return products

    # POST /api/products/
    @blp.arguments(ProductSchema)
    @blp.response(201, ProductSchema)
    def post(self, new_product):
        """Đăng sản phẩm mới"""
        new_product["id"] = max(
            [product["id"] for product in products],
            default=0
        ) + 1

        products.append(new_product)

        return new_product