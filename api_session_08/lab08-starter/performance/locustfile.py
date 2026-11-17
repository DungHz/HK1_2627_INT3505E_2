"""Lab 4: weighted tasks + search_by_year with a 1% simulated failure.

Run: locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
         -u 10 -r 2 -t 30s --html reports/A.html

GHI CHÚ VỀ FAILURE GIẢ LẬP:
search_by_year đánh dấu khoảng 1% request là failure bằng response.failure()
ở PHÍA CLIENT (Locust). Server KHÔNG trả HTTP 500 cho các request này; server
vẫn trả 200. Trong báo cáo Locust, các failure này có thông báo
"SIMULATED client-side failure" để phân biệt với lỗi HTTP thật.
"""
import itertools
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)
SIMULATED_FAILURE_RATE = 0.01
YEARS = list(range(2015, 2026))


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # 404 là hành vi mong đợi (id ngẫu nhiên có thể không tồn tại).
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={
                "title": f"Load test {unique}",
                "author": "locust",
                "year": random.choice(YEARS),
            },
            name="POST /books",
        )

    @task(1)
    def search_by_year(self):
        year = random.choice(YEARS)
        with self.client.get(
            f"/books?year={year}", name="GET /books?year={year}", catch_response=True
        ) as response:
            if response.status_code != 200:
                # Lỗi HTTP THẬT do server trả về (ví dụ 500 khi SQLite bị khoá).
                response.failure(f"HTTP {response.status_code} from server")
            elif not isinstance(response.json(), list):
                response.failure("Body is not a JSON array")
            elif random.random() < SIMULATED_FAILURE_RATE:
                # Failure GIẢ LẬP phía client: server vẫn trả 200.
                response.failure("SIMULATED client-side failure (server returned 200)")
            else:
                response.success()
