# Hướng Dẫn Đưa Website Tùng Phạm Algo Lab Lên Online & Gắn Tên Miền Riêng

Tài liệu này hướng dẫn Mr Tung từng bước đưa hệ thống **SMC & PA Weekly Trading Terminal** lên mạng Internet hoàn toàn **MIỄN PHÍ** (hoặc chi phí cực rẻ) và gắn tên miền riêng (ví dụ: `tungphamalgolab.com` hoặc `trading.tungpham.vn`) để 400 thành viên trong cộng đồng truy cập 24/7.

---

## ⭐️ Cách 1: Đưa Lên Render.com (Miễn Phí 100% - Khuyên Dùng)

**Render.com** là nền tảng máy chủ đám mây hiện đại hỗ trợ ứng dụng Python FastAPI cực kỳ mượt mà và miễn phí.

### Bước 1: Đưa Mã Nguồn Lên GitHub
1. Tạo tài khoản miễn phí trên [github.com](https://github.com) (nếu chưa có).
2. Tạo một Repository mới (đặt tên: `tungpham-algo-lab`, chọn chế độ **Private** hoặc **Public**).
3. Mở Terminal trên máy Mac của anh tại thư mục này và chạy các lệnh:
   ```bash
   git init
   git add .
   git commit -m "Khoi tao he thong Tung Pham Algo Lab"
   git branch -M main
   git remote add origin https://github.com/<tai_khoan_cua_anh>/tungpham-algo-lab.git
   git push -u origin main
   ```

### Bước 2: Tạo Web Service Trên Render.com
1. Truy cập [render.com](https://render.com) và đăng nhập bằng tài khoản GitHub.
2. Bấm nút **New +** -> Chọn **Web Service**.
3. Chọn Repository `tungpham-algo-lab` vừa tạo.
4. Điền các thông số:
   - **Name:** `tungpham-algo-lab`
   - **Region:** `Singapore` (để người dùng Việt Nam truy cập nhanh nhất)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** `Free`
5. Tại mục **Environment Variables (Biến môi trường)**:
   - Thêm key: `ADMIN_PASSWORD` -> value: `mat_khau_cua_anh` (ví dụ: `tungpham8888`)
6. Bấm **Create Web Service**. Đợi khoảng 1-2 phút, Render sẽ cấp cho anh đường link miễn phí dạng:
   👉 `https://tungpham-algo-lab.onrender.com`

---

## 🌐 Cách 2: Gắn Tên Miền Riêng (Custom Domain)

Sau khi web đã chạy trên Render, anh có thể gắn tên miền thương hiệu riêng:

1. **Mua tên miền:** Anh có thể mua tên miền dạng `.com` hoặc `.vn` tại Namecheap, Cloudflare, hoặc Nhà đăng ký Việt Nam (PA Việt Nam, Mắt Bão, Vietnix...) với giá chỉ ~200k - 300k/năm.
2. **Cấu hình trên Render:**
   - Vào Dashboard của Web Service trên Render -> Chọn tab **Settings** -> Mục **Custom Domains**.
   - Bấm **Add Custom Domain** và nhập tên miền của anh (ví dụ: `tungphamalgolab.com` hoặc `trading.tungpham.vn`).
3. **Cấu hình DNS tại nơi mua tên miền:**
   - Thêm bản ghi **CNAME**:
     - **Name / Host:** `@` hoặc `trading`
     - **Target / Value:** `tungpham-algo-lab.onrender.com`
4. Render sẽ tự động cấp chứng chỉ bảo mật **SSL (HTTPS 🔒)** miễn phí trong 5 phút.

---

## 🔐 Cơ Chế Quản Trị & Bảo Vệ Dành Riêng Cho Mr Tung

- **400 Thành viên truy cập:**
  - Được xem toàn bộ biểu đồ trực tiếp, các vùng Order Block H4, nến Price Action, Lịch kinh tế tin đỏ và tin tức thị trường.
  - Không thể chỉnh sửa hoặc xóa dữ liệu.
- **Mr Tung (Admin):**
  - Nhấp vào nút **Mr Tung Login** ở góc trên bên phải màn hình (hoặc bấm nút "Chỉnh Sửa Kịch Bản").
  - Nhập mật khẩu quản trị (`ADMIN_PASSWORD`).
  - Hệ thống sẽ cấp huy hiệu **👑 Mr Tung (Admin)** để anh toàn quyền thay đổi kịch bản BUY/SELL, vùng Entry, SL, TP, checklist và ghi chú chiến thuật.
