## 2 quyết định khó nhất
# 1 Lựa chọn status cho từng trường hợp

API không trả về một mã trạng thái chung chung (như 200 OK cho mọi trường hợp), mà tận dụng triệt để ý nghĩa ngữ nghĩa của HTTP Status Code nhằm giúp phía Client dễ dàng xử lý ngoại lệ và nắm bắt kết quả request ngay lập tức:

200 OK: Dùng cho các thao tác truy vấn dữ liệu thành công (lấy danh sách hoặc chi tiết task) hoặc cập nhật tài nguyên thành công.

201 Created: Trả về khi khởi tạo thành công một Task mới (đi kèm đường dẫn hoặc thông tin tài nguyên vừa tạo).

204 No Content: Trả về khi xóa thành công một Task, xác nhận request đã được xử lý hoàn tất nhưng không cần trả về response body.

404 Not Found: Trả về khi không tìm thấy tài nguyên tương ứng với định danh taskId được truyền vào.

422 Unprocessable Entity: Trả về khi cấu trúc/định dạng dữ liệu gửi lên hợp lệ nhưng vi phạm các quy tắc kiểm tra logic/validation nghiệp vụ của hệ thống.

Cách thiết kế này giúp giao tiếp giữa Client và Server trở nên minh bạch, tường minh, đồng thời tối ưu hóa quá trình kiểm thử tự động (automated testing) và gỡ lỗi (debugging).

# 2 Phân chia rõ ràng Dữ liệu Đầu vào (Input) và Đầu ra (Output)

Nếu dùng chung 1 cấu trúc dữ liệu cho cả lúc tạo mới, cập nhật và hiển thị, API dễ bị thừa dữ liệu không cần thiết (như người dùng truyền nhầm ID khi tạo) hoặc làm rò rỉ các thông tin nội bộ của hệ thống.

Tách riêng các Model dữ liệu cho từng thao tác:   
CreateTask: Chỉ chứa thông tin cần để tạo task mới.   
UpdateTask: Cho phép sửa từng phần thông tin.   
Task: Chứa đầy đủ thông tin hoàn chỉnh trả về cho Client. 