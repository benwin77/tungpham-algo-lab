# HƯỚNG DẪN CÀI ĐẶT & BACKTEST CTRADER BOT (SMC & PRICE ACTION) 🚀

Tài liệu này hướng dẫn anh Tùng cách đưa file bot **`TungPhamAlgoLab_SMC_Bot.cs`** vào phần mềm **cTrader Automate** để backtest kiểm thử hiệu suất và chạy thực chiến.

---

## 📌 1. LOGIC THỰC CHIẾN CỦA BOT (SMART MONEY CONCEPTS):

Bot hoạt động theo đúng 5 bước chuẩn hóa của hệ thống **Tùng Phạm Algo Lab**:

1. **Bộ lọc Xu Hướng Macro (Trend Filter):**
   * **BUY:** Nến đóng cửa > EMA 50 > EMA 200 (Uptrend Structure).
   * **SELL:** Nến đóng cửa < EMA 50 < EMA 200 (Downtrend Structure).

2. **Săn Thanh Khoản / Quét Râu Đáy Đỉnh (Liquidity Sweep / SFP):**
   * Quét sạch thanh khoản Sell-side Liquidity (SSL) ở đáy cũ hoặc Buy-side Liquidity (BSL) ở đỉnh cũ rồi rút chân đóng nến trở lại bên trong.

3. **Xác Định Vùng Cầu / Cung Order Block (OB) & Khoảng Trống Giá (FVG):**
   * Tự động quét tìm cây nến cuối cùng trước nhịp đẩy giá mạnh tạo khoảng trống mất cân bằng Imbalance (FVG).

4. **Kích Hoạt Vào Lệnh (Execution Trigger):**
   * Khi giá điều chỉnh (Pullback) về kiểm tra lại vùng **Demand Order Block** (đối với BUY) hoặc **Supply Order Block** (đối với SELL).
   * Xuất hiện nến xác nhận cùng chiều.

5. **Quản Trị Vốn & Quản Lý Lệnh Chuẩn Quỹ:**
   * **Tính Lot Tự Động:** Tính chính xác khối lượng Lot theo đúng `% Rủi Ro Tài Khoản` (mặc định 1.0% / lệnh).
   * **Stop Loss:** Đặt an toàn dưới chân Order Block + Đệm ATR (`1.5x ATR`).
   * **Take Profit 1 (+1.5R):** Khi giá chạm +1.5R ➔ **Tự động chốt 50% khối lượng** và **dời Stop Loss về vùng Entry hòa vốn (Breakeven - 0% rủi ro)**.
   * **Take Profit 2 (+3.5R):** Gồng lãi trọn vẹn đến mục tiêu thanh khoản lớn.

---

## 🛠 2. CÁCH CÀI ĐẶT VÀO CTRADER:

1. Mở phần mềm **cTrader** trên máy tính (hoặc cTrader Web).
2. Nhìn cột menu bên trái, chọn biểu tượng **Automate** (hình chiếc cờ lê / bánh răng).
3. Bấm nút **`+ New`** (hoặc `New cBot`).
4. Đặt tên bot là: **`TungPhamAlgoLab_SMC_Bot`**.
5. Mở file [TungPhamAlgoLab_SMC_Bot.cs](file:///Users/macbook/Desktop/Web%20news/cbot/TungPhamAlgoLab_SMC_Bot.cs), copy toàn bộ nội dung code C# và dán đè vào trình soạn thảo code của cTrader.
6. Bấm nút **`Build`** (Phím tắt `Ctrl + B` hoặc `F6` trên Windows / Mac) ➔ Khi thấy thông báo `Build succeeded` màu xanh lá là thành công!

---

## 🧪 3. HƯỚNG DẪN BACKTEST KIỂM THỬ:

1. Trong tab Automate của cTrader, nhấp vào bot **`TungPhamAlgoLab_SMC_Bot`**.
2. Chọn biểu tượng **`+ Add an Instance`**.
3. Chọn cặp tiền / tài sản muốn test:
   * **XAUUSD (Vàng):** Khung thời gian khuyến nghị: **H1** hoặc **M15** / **H4**.
   * **US100 (Nasdaq):** Khung **M15** hoặc **H1**.
   * **BTCUSD (Bitcoin):** Khung **H1** hoặc **H4**.
   * **GBPUSD / USDJPY / CADCHF:** Khung **H1**.
4. Chuyển sang Tab **`Backtesting`**:
   * Chọn khoảng thời gian (ví dụ: 1 năm qua từ 01/01/2025 đến nay).
   * Chọn chế độ dữ liệu: **Tick Data (from Server)** để độ chính xác cao nhất.
   * Chọn số vốn ban đầu: `$10,000` hoặc `$100,000` (chuẩn tài khoản Quỹ).
5. Bấm nút **`Play ▶️`** để bắt đầu Backtest.
6. Xem kết quả tại Tab **`Equity`** (Đường cong tăng trưởng vốn) và **`Performance History`** (Winrate, Profit Factor, Max Drawdown, Net Profit).

---

## ⚙️ 4. BẢNG THÔNG SỐ ĐỀ XUẤT (OPTIMAL PARAMETERS):

| Thông Số | Giá Trị Đề Xuất | Ý Nghĩa |
| :--- | :--- | :--- |
| `Account Risk (%)` | `1.0%` | Rủi ro tối đa mỗi lệnh trên tổng vốn |
| `Reward-to-Risk (TP2)` | `3.5` | Mục tiêu chốt lời toàn phần (1 ăn 3.5) |
| `Enable Partial TP1` | `True` | Bật chốt 50% khối lượng tại +1.5R |
| `Move SL to Breakeven` | `True` | Tự động dời SL về hòa vốn khi đạt TP1 |
| `Order Block Lookback` | `30 bars` | Số nến quét tìm vùng Order Block |
| `ATR Buffer for SL` | `1.5` | Hệ số khoảng đệm ATR bảo vệ chân SL |
| `Filter Trading Hours` | `True` | Chỉ đánh phiên London & New York (07:00 - 20:00 UTC) |
| `Max Spread` | `3.5 pips` | Tránh vào lệnh khi thị trường giãn spread |
