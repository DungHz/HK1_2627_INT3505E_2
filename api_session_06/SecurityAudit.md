# Security Audit

## 1. Lộ mật khẩu

**Rủi ro:** Mật khẩu có thể bị lộ nếu lưu hoặc ghi vào log dưới dạng văn
bản thường.

**Cách khắc phục:** Không ghi mật khẩu vào log; lưu mật khẩu bằng thuật
toán băm an toàn.

## 2. Lộ access token

**Rủi ro:** Người khác có thể dùng token bị lộ để truy cập API trái
phép.

**Cách khắc phục:** Dùng HTTPS; không đặt token trong URL hoặc ghi token
vào log.

## 3. Lộ refresh token

**Rủi ro:** Kẻ xấu có thể dùng refresh token bị đánh cắp để lấy access
token mới.

**Cách khắc phục:** Bảo vệ refresh token, thu hồi token khi phát hiện bị
lộ và tránh ghi token vào log.

## 4. Dò tài khoản

**Rủi ro:** Thông báo đăng nhập có thể tiết lộ tài khoản có tồn tại hay
không.

**Cách khắc phục:** Dùng thông báo lỗi chung khi đăng nhập thất bại.

## 5. Truy cập bài viết trái phép

**Rủi ro:** Người dùng có thể xem bài viết riêng tư nếu API không kiểm
tra quyền.

**Cách khắc phục:** Kiểm tra danh tính và quyền truy cập trước khi trả
bài viết.

## 6. Lộ thông tin nội bộ qua lỗi

**Rủi ro:** Thông báo lỗi chi tiết có thể làm lộ cấu trúc hệ thống hoặc
dữ liệu nhạy cảm.

**Cách khắc phục:** Chỉ trả thông báo lỗi cần thiết; không gửi stack
trace cho client.

## 7. Thử mật khẩu liên tục

**Rủi ro:** Kẻ xấu có thể thử nhiều mật khẩu để chiếm tài khoản.

**Cách khắc phục:** Giới hạn số lần đăng nhập và áp dụng rate limit.

## 8. Trả về quá nhiều dữ liệu

**Rủi ro:** API có thể vô tình tiết lộ thông tin cá nhân hoặc dữ liệu
không cần thiết.

**Cách khắc phục:** Chỉ trả các trường dữ liệu cần thiết của bài viết.

## 9. Lộ thông tin bí mật trên Git

**Rủi ro:** Mật khẩu, token hoặc khóa bí mật bị commit có thể bị người
khác lấy được.

**Cách khắc phục:** Không commit thông tin bí mật; dùng biến môi trường
hoặc kho lưu trữ bí mật.
