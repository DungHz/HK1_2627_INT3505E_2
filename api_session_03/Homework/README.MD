## Review Spotify Web API theo 9 tiêu chí

# 1 Tài nguyên là danh từ

Spotify Web API tổ chức API theo tài nguyên như artists, albums, tracks, playlists, users, shows... URL chủ yếu dùng danh từ, không dùng động từ.

Ví dụ:

GET /v1/artists/{id}
GET /v1/albums/{id}
GET /v1/tracks/{id}
GET /v1/playlists/{id}

đánh giá: Tốt

# 2 Naming nhất quán

Spotify sử dụng cách đặt tên khá nhất quán:

Path dùng dạng số nhiều: artists, albums, tracks, playlists.
Resource con dùng cấu trúc rõ ràng:
GET /v1/artists/{id}/albums
GET /v1/playlists/{id}/items
Query parameter sử dụng dạng snake_case ở một số trường hợp như album_type, include_groups, market.

Spotify cũng sử dụng /v1/ trong Base URL:

https://api.spotify.com/v1/...

Tuy nhiên, naming không hoàn toàn tuyệt đối đồng nhất do API có lịch sử phát triển lâu dài và đã có một số endpoint bị đổi tên/deprecated. Ví dụ /playlists/{id}/tracks đã được thay bằng /playlists/{id}/items.

đánh giá: khá tốt do vẫn còn một vài endpoint cũ

# 3 Status code đúng nghĩa

Spotify sử dụng nhiều HTTP status code có ý nghĩa rõ ràng:

200 OK – request thành công.
201 Created – tạo resource thành công.
204 No Content – thành công nhưng không có body.
400 Bad Request – request không hợp lệ.
401 Unauthorized – lỗi xác thực.
403 Forbidden – không có quyền.
404 Not Found – không tìm thấy resource.
429 Too Many Requests – vượt rate limit.
500/502/503 – lỗi phía server.

Đánh giá: Rất tốt.

# 4 Idempotency rõ ràng

Spotify sử dụng:

GET
PUT
DELETE

theo đúng ý nghĩa HTTP. Trong tài liệu, PUT được dùng để thay đổi/thay thế resource hoặc collection, còn DELETE để xóa resource.

Tuy nhiên, Spotify không nổi bật việc hỗ trợ Idempotency-Key như Stripe.

Ví dụ với các thao tác ghi dữ liệu, tài liệu Spotify không cho thấy một cơ chế Idempotency-Key chung để client gửi lại request mà vẫn đảm bảo tránh xử lý trùng.

Spotify có cơ chế snapshot cho playlist để kiểm soát phiên bản và các thay đổi đồng thời, nhưng đây không phải là Idempotency-Key.

Đánh giá: Khá – HTTP method có ý nghĩa rõ nhưng chưa có cơ chế idempotency-key chung như một số API hiện đại.

# 5 Error response có cấu trúc

Spotify có cấu trúc error response tương đối rõ ràng.

Ví dụ:

{
  "error": {
    "status": 400,
    "message": "invalid id"
  }
}

Ngoài status và message, một số lỗi còn có reason, ví dụ QUOTA_EXCEEDED. Spotify cũng có format riêng cho lỗi authentication với:

{
  "error": "invalid_client",
  "error_description": "Invalid client secret"
}

Tuy nhiên, Spotify không sử dụng RFC 7807 application/problem+json với các trường như:

type
title
detail
instance

Đánh giá: Khá tốt – error có cấu trúc nhưng chưa theo RFC 7807.

# 6 Pagination rõ ràng

Spotify hỗ trợ pagination trên nhiều collection.

Các tham số phổ biến:

?offset=0&limit=20

Response thường chứa:

{
  "href": "...",
  "limit": 20,
  "next": "...",
  "offset": 0,
  "previous": null,
  "total": 100,
  "items": [...]
}

next, previous, limit, offset và total giúp client dễ dàng lấy trang tiếp theo.

Spotify cũng đặt giới hạn limit tùy endpoint. Ví dụ một số endpoint có tối đa 50 phần tử, trong khi Search hiện có giới hạn thấp hơn sau thay đổi năm 2026.

Đánh giá:  Rất tốt – pagination rõ ràng và có giới hạn.

# 7 Filter/Sort đa dạng

Spotify hỗ trợ nhiều query parameter để lọc và điều khiển dữ liệu.

Ví dụ:

GET /v1/artists/{id}/albums?album_type=album&limit=20&offset=0

Đặc biệt, API playlist còn hỗ trợ fields để lựa chọn những field muốn nhận:

GET /v1/playlists/{id}/items?fields=items(track(name,href))

Điều này giúp client không cần nhận toàn bộ object nếu chỉ cần một số trường.

Tuy nhiên, khả năng sort tùy ý theo nhiều field không mạnh như một số API CRUD tổng quát. Spotify chủ yếu cung cấp các filter/query parameter phù hợp với từng resource.

Đánh giá:  Khá – filter tốt, nhưng sort linh hoạt chưa phải điểm mạnh.

# 8 Authentication & Security

Spotify sử dụng OAuth 2.0, đây là một điểm mạnh lớn.

Các flow được hỗ trợ gồm:

Authorization Code
Authorization Code + PKCE
Client Credentials

Access token được gửi qua HTTP header:

Authorization: Bearer <access_token>

Token có thời hạn và cần refresh khi hết hạn.

Spotify cũng sử dụng scope để giới hạn quyền của ứng dụng, ví dụ ứng dụng chỉ được cấp những quyền cần thiết.

Ngoài ra API có rate limit và trả 429 khi vượt giới hạn, thường kèm Retry-After để client biết thời gian chờ.

Đánh giá:  Rất tốt – OAuth 2.0, scope, Bearer token và rate limit được triển khai rõ ràng.

# 9 Versioning + Deprecation
Spotify sử dụng version prefix:

https://api.spotify.com/v1/...

Đây là cách versioning dễ hiểu và giúp phân biệt phiên bản API.

Spotify cũng có cơ chế deprecation và migration khá rõ. Ví dụ năm 2026, Spotify thay đổi nhiều endpoint:

/playlists/{id}/tracks

được thay bằng:

/playlists/{id}/items

Một số endpoint cũ được đánh dấu Deprecated và Spotify cung cấp endpoint thay thế cùng migration guide.

Tuy nhiên, việc API thay đổi khá mạnh trong năm 2026 cho thấy developer cần thường xuyên theo dõi changelog và migration guide để tránh ứng dụng bị ảnh hưởng.

Đánh giá:  Tốt – có versioning, deprecation và tài liệu migration rõ ràng, nhưng việc thay đổi endpoint có thể tạo chi phí bảo trì.