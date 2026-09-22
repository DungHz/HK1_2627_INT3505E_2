# Audit GitHub REST API

**1. Endpoint: Lấy thông tin một người dùng**
* **Method:** GET
* **URL:** `/users/{username}`
* **Status codes:** 200 OK (Thành công), 404 Not Found (Không tìm thấy user).
* **Headers:** `Accept: application/vnd.github+json`, `Authorization: Bearer <token>`
* **Đánh giá RESTful:** **Có.** GET là phương thức Safe và Idempotent, được sử dụng để truy xuất resource. URI `/users/{username}` sử dụng danh từ để định danh resource người dùng.

**2. Endpoint: Tạo Repository mới cho User xác thực**
* **Method:** POST
* **URL:** `/user/repos`
* **Status codes:** 201 Created (Tạo thành công), 401 Unauthorized, 422 Unprocessable Entity (Dữ liệu không hợp lệ).
* **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
* **Đánh giá RESTful:** **Có.** Dùng POST để tạo resource mới trong collection `/user/repos`. Khi tạo thành công, API trả về mã 201 Created cùng thông tin của repository vừa được tạo.

**3. Endpoint: Cập nhật thông tin Repository**
* **Method:** PATCH
* **URL:** `/repos/{owner}/{repo}`
* **Status codes:** 200 OK, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity.
* **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
* **Đánh giá RESTful:** **Có.** PATCH phù hợp cho việc sửa đổi một phần resource, chẳng hạn như đổi tên repository hoặc chỉnh sửa phần mô tả mà không cần gửi toàn bộ dữ liệu của repository.

**4. Endpoint: Xóa Repository**
* **Method:** DELETE
* **URL:** `/repos/{owner}/{repo}`
* **Status codes:** 204 No Content (Xóa thành công), 403 Forbidden, 404 Not Found.
* **Headers:** `Accept: application/vnd.github+json`, `Authorization: Bearer <token>`
* **Đánh giá RESTful:** **Có.** DELETE là phương thức Idempotent, được sử dụng để xóa resource. Khi xóa thành công, API trả về 204 No Content, nghĩa là request thành công nhưng không có nội dung trong response body.

**5. Endpoint: Khóa một Issue**
* **Method:** PUT
* **URL:** `/repos/{owner}/{repo}/issues/{issue_number}/lock`
* **Status codes:** 204 No Content, 403 Forbidden, 404 Not Found.
* **Headers:** `Content-Type: application/json`, `Authorization: Bearer <token>`
* **Đánh giá RESTful:** **RESTful-ish.** PUT là phương thức Idempotent và được sử dụng để thay đổi trạng thái của Issue. Tuy nhiên, `/lock` mang tính chất action hơn là tên resource. Đây là cách thiết kế phổ biến trong thực tế, nhưng không thuần REST như các endpoint sử dụng URI chủ yếu để định danh resource.