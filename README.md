# Website Phong Thủy Việt

Website tiếng Việt chuyên chia sẻ kiến thức phong thủy (mang tính tham khảo văn hóa), có hệ thống tạo bài tự động hàng ngày và theo dõi Trang Facebook công khai.

## Yêu cầu hệ thống

- Python 3.10+
- pip
- Máy chủ Linux (cho cron) hoặc dịch vụ tương đương

## Cài đặt

1. **Clone hoặc tải mã nguồn**

```bash
cd /đường/dẫn/bạn/muốn
# (Các file đã nằm trong thư mục phongthuy_site)
```

2. **Tạo môi trường ảo và cài thư viện**

```bash
cd phongthuy_site
python3 -m venv venv
source venv/bin/activate   # Trên Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Cấu hình môi trường (tùy chọn)**

Tạo file `.env`:

```
SECRET_KEY=your-very-secret-key-here
DATABASE_URL=sqlite:///phongthuy.db
```

4. **Khởi tạo cơ sở dữ liệu**

```bash
python app.py
```

Lần chạy đầu sẽ tự tạo database SQLite và tài khoản admin mặc định:

- Username: `admin`
- Password: `admin123`

**Đổi mật khẩu ngay sau khi đăng nhập!**

5. **Chạy thử**

```bash
python app.py
```

Truy cập: http://localhost:5000

Admin: http://localhost:5000/admin/login

## Triển khai production

Khuyến nghị dùng Gunicorn + Nginx:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Cấu hình Nginx reverse proxy và HTTPS (Let's Encrypt).

## Cấu hình tác vụ chạy hàng ngày

**Website không tự động tạo bài hoặc kiểm tra Facebook nếu chưa thiết lập cron hoặc dịch vụ lập lịch trên máy chủ.**

### 1. Tạo bài viết hàng ngày

```bash
crontab -e
```

Thêm dòng (thay đường dẫn thực tế):

```
0 8 * * * cd /path/to/phongthuy_site && /path/to/phongthuy_site/venv/bin/python generate_daily.py >> /var/log/phongthuy_daily.log 2>&1
```

Giờ có thể điều chỉnh trong Admin → Cài đặt.

### 2. Theo dõi Facebook

```
0 */6 * * * cd /path/to/phongthuy_site && /path/to/phongthuy_site/venv/bin/python fb_monitor.py >> /var/log/phongthuy_fb.log 2>&1
```

## Tích hợp Facebook

1. Tạo ứng dụng trên [Meta for Developers](https://developers.facebook.com/).
2. Xin quyền **Page Public Content Access** (cần review).
3. Lấy Page Access Token của trang bạn muốn theo dõi (trang công khai).
4. Vào Admin → Facebook → thêm tên, Page ID và Access Token.
5. Hệ thống sẽ tạo **bản tóm tắt** (không đăng nguyên văn) và đưa vào hàng chờ duyệt.

**Không hỗ trợ:** nhóm riêng tư, vượt CAPTCHA, đăng nhập không phép, lấy ảnh/video có bản quyền.

Nếu API báo lỗi, lỗi sẽ được ghi log và hiển thị trong hệ thống.

## Tính năng chính

- Tạo bài tự động từ danh sách chủ đề (tránh trùng lặp).
- Trạng thái “Chờ duyệt” mặc định. Có thể bật tự đăng trong Cài đặt.
- SEO: URL thân thiện, meta, sitemap.xml, Open Graph.
- Bình luận có kiểm duyệt.
- Responsive (Tailwind CSS).
- Disclaimer rõ ràng trên mọi bài viết.

## Mở rộng nội dung tự động

Hiện tại `generate_daily.py` và `create_post_from_topic()` dùng mẫu cố định. Để có bài chất lượng cao hơn:

- Tích hợp API LLM (xAI Grok, OpenAI, v.v.) trong hàm tạo nội dung.
- Thêm nhiều chủ đề vào danh sách `TOPICS` trong `app.py`.
- Dùng ảnh từ Unsplash/Pexels (đã có giấy phép rõ ràng) hoặc tạo ảnh AI riêng.

## Bảo mật

- Đổi `SECRET_KEY`.
- Đổi mật khẩu admin ngay.
- Không commit file `.env` hoặc database.
- Dùng HTTPS khi triển khai.
- Hạn chế quyền truy cập thư mục admin nếu cần.

## Lưu ý pháp lý và nội dung

Tất cả bài viết đều chứa disclaimer: đây là quan niệm văn hóa/tham khảo, không phải khoa học đã chứng minh, không hứa hẹn tài lộc/sức khỏe/tình duyên, không thay thế tư vấn chuyên môn.

Không bịa nguồn hoặc số liệu.

---

Mã nguồn được xây dựng để dễ tùy chỉnh và triển khai. Chúc bạn vận hành thành công!
