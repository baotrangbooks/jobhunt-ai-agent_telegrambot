# Hướng Dẫn & Thông Tin Triển Khai Hệ Thống (Server & Deployment Operations)

Tài liệu này ghi nhớ toàn bộ thông số máy chủ, quy trình triển khai (deploy), cấu hình dịch vụ và nguyên tắc an toàn vận hành cho toàn bộ hệ thống dự án `Bottimviec.ai`.

---

## 1. Thông Tin Máy Chủ (Server Credentials & Paths)

- **Địa chỉ IP Server**: `123.30.233.101`
- **Tài khoản SSH**: `duongnv`
- **Mật khẩu**: `duongvnn`
- **Thư mục người dùng**: `/home/duongnv`

### Bố cục thư mục trên Server:
| Thành phần | Thư mục trên Server | Dự án Local tương ứng |
| :--- | :--- | :--- |
| **Backend Core** | `/home/duongnv/hhbackend` | `FastAPI-boilerplate` |
| **Agent Assistant Library** | `/home/duongnv/hhbackend/vendor/ai-agent-assistant` | `ai-agent-assistant` |
| **User Frontend (Staging/Upload)** | `/tmp/hh-user-frontend` | `jobhunt-ai-agent_enduser` |
| **Admin Frontend (Staging/Upload)**| `/tmp/hh-admin-frontend` | `hh-admin-frontend` |
| **Deploy Scripts** | `/home/duongnv/` | `rebuild-user-frontend.sh`, `rebuild-admin-frontend.sh` |

---

## 2. Quy Trình Cập Nhật & Triển Khai (Deployment Procedures)

### A. Triển khai Backend (`FastAPI-boilerplate` & `ai-agent-assistant`)
1. Upload code đã cập nhật từ máy dev lên server bằng `scp` hoặc `rsync`:
   - Backend: upload vào `/home/duongnv/hhbackend/`
   - Thư viện: upload vào `/home/duongnv/hhbackend/vendor/ai-agent-assistant/`
2. Kết nối SSH vào server và khởi động lại container:
   ```bash
   cd /home/duongnv/hhbackend
   docker compose restart web
   ```

### B. Triển khai WebApp Người Dùng (`jobhunt-ai-agent_enduser`)
1. Upload mã nguồn frontend lên thư mục tạm:
   - Đích đến: `/tmp/hh-user-frontend`
2. Đăng nhập SSH và thực thi script build:
   ```bash
   cd /home/duongnv
   sudo ./rebuild-user-frontend.sh
   ```

### C. Triển khai WebApp Quản Trị (`hh-admin-frontend`)
1. Upload mã nguồn frontend admin lên thư mục tạm `/tmp/hh-admin-frontend`
2. Đăng nhập SSH và thực thi script build:
   ```bash
   cd /home/duongnv
   sudo ./rebuild-admin-frontend.sh
   ```

---

## 3. Kết Nối Dữ Liệu Thực Qua SSH Local Port Forwarding

Để kiểm thử trực tiếp trên máy phát triển (localhost) với dữ liệu thực tế từ Cloud mà không cần mở public port:
- Có thể dùng SSH Tunneling đưa các service trên server về localhost:
  ```powershell
  # Forward MySQL (3306), TypeSense (8108), Redis (6379) về localhost:
  ssh -L 3306:localhost:3306 -L 8108:localhost:8108 -L 6379:localhost:6379 duongnv@123.30.233.101
  ```
- Toàn bộ thông tin cấu hình liên quan (OpenAI API key, LangSmith, TypeSense API key, Redis, Firebase) được quản lý trong file `.env` của các dự án.

---

## 4. Nguyên Tắc An Toàn Bắt Buộc (Safety & Protection Rules)

> [!CAUTION]
> **QUY TẮC AN TOÀN TUYỆT ĐỐI**:
> - Nghiêm cấm tự ý thực thi các lệnh có nguy cơ phá hủy hoặc xóa dữ liệu như `DELETE FROM`, `DROP TABLE`, `rm -rf` trên các file hoặc bảng dữ liệu quan trọng của server.
> - Bất kỳ thao tác can thiệp trực tiếp đến cơ sở dữ liệu sản xuất hoặc cấu trúc container trọng yếu đều **bắt buộc phải hỏi và có xác nhận rõ ràng từ người dùng**.
