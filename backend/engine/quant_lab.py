import os
import json
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
QUANT_LAB_FILE = os.path.join(DATA_DIR, "quant_lab.json")

INITIAL_QUANT_STRATEGIES: List[Dict[str, Any]] = [
    {
        "id": "quant_vn30f",
        "name": "VN30F Intraday Momentum & Liquidity Algo",
        "market": "Phái Sinh Việt Nam (VN30F1M)",
        "timeframe": "M5 / M15 Systematic",
        "period": "2021 – 2026 (5 Năm Thực Chiến)",
        "total_trades": 1284,
        "win_rate": "54.8%",
        "profit_factor": 1.78,
        "max_drawdown": "14.2%",
        "expectancy": "+0.42R / Trade",
        "sharpe_ratio": 2.14,
        "net_profit_r": "+539.4R",
        "description": "Thuật toán khai thác dòng tiền lớn (Smart Money Liquidity) trong phiên sáng và chiều của thị trường chứng khoán phái sinh Việt Nam, tự động cắt lỗ cố định và gồng lãi theo bước sóng Fibonacci.",
        "badge": "Algo Chiến Lược HFT"
    },
    {
        "id": "quant_xauusd",
        "name": "XAU/USD London-NY Killzone Breakout & Sweep",
        "market": "Vàng Giao Ngay (Spot Gold)",
        "timeframe": "H1 / M15 Execution",
        "period": "2020 – 2026 (6 Năm Backtest)",
        "total_trades": 1842,
        "win_rate": "58.4%",
        "profit_factor": 2.15,
        "max_drawdown": "16.8%",
        "expectancy": "+0.58R / Trade",
        "sharpe_ratio": 2.38,
        "net_profit_r": "+1068.3R",
        "description": "Chiến lược định lượng chuyên săn bẫy giá Judas Swing phiên London (13:00 - 15:30 VN) và bùng nổ xung lực phiên Mỹ (19:30 - 22:00 VN). Tối ưu hóa tỷ lệ R:R tối thiểu 1:2.5.",
        "badge": "Algo Đỉnh Cao Vàng"
    },
    {
        "id": "quant_us100",
        "name": "US100 (Nasdaq) Volatility Trend Following",
        "market": "Nasdaq 100 Index CFD",
        "timeframe": "H4 / H1 Trend",
        "period": "2019 – 2026 (7 Năm Backtest)",
        "total_trades": 962,
        "win_rate": "51.2%",
        "profit_factor": 2.32,
        "max_drawdown": "18.5%",
        "expectancy": "+0.64R / Trade",
        "sharpe_ratio": 2.05,
        "net_profit_r": "+615.6R",
        "description": "Bắt trọn các đợt sóng siêu chu kỳ của nhóm cổ phiếu Big Tech Mỹ, kết hợp bộ lọc động lượng EMA Cloud và quy tắc quản trị rủi ro cố định 1% vốn / vị thế.",
        "badge": "Trend Khung Lớn"
    }
]

def load_quant_lab_data() -> List[Dict[str, Any]]:
    if os.path.exists(QUANT_LAB_FILE):
        try:
            with open(QUANT_LAB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[QuantLab] Warning reading file: {e}")
            
    save_quant_lab_data(INITIAL_QUANT_STRATEGIES)
    return INITIAL_QUANT_STRATEGIES

def save_quant_lab_data(data: List[Dict[str, Any]]):
    try:
        os.makedirs(os.path.dirname(QUANT_LAB_FILE), exist_ok=True)
        with open(QUANT_LAB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[QuantLab] Error saving file: {e}")
