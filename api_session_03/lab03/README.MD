## Triển khai /orders có cursor pagination
# (1) cursor; 
Lấy chỉ 3 dữ liệu
![alt text](image-1.png)

Lẩy tiếp 3 dữ liệu sau id = 3
![alt text](image-2.png)
# (2) filter: status, customer_id; 
Lấy theo status
![alt text](image-3.png)

Lây theo cus_id
![alt text](image-4.png)
# (3) sort; 
Sort theo total từ lớn tới bé
![alt text](image-5.png)
# (4) sparse fieldsets
Lấy dữ liệu cỉ cần trả về id và total
![alt text](image-6.png)

# (5) 400 BAD REQUEST
![alt text](image-7.png)