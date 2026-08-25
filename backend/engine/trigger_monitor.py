import os
import requests
from typing import Dict, Any
from datetime import datetime

# In-memory alert cooldown tracker: { "XAUUSD": timestamp }
LAST_ALERTED: Dict[str, float] = {}
ALERT_COOLDOWN_SECONDS = 3600 # 1 hour per pair to prevent spamming

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    if not bot_token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        res = requests.post(url, json=payload, timeout=8)
        return res.ok
    except Exception as e:
        print(f"[TriggerMonitor] Error sending Telegram message: {e}")
        return False

def check_and_send_trigger_alerts(market_data: Dict[str, Any], forecasts: Dict[str, Any]) -> Dict[str, Any]:
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        return {"active": False, "reason": "Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID"}

    now_ts = datetime.now().timestamp()
    triggered_alerts = []

    for pair, f in forecasts.items():
        m = market_data.get(pair, {})
        current_price = m.get("current_price") or f.get("current_price")
        if not current_price:
            continue

        entry_low = f.get("entry_low")
        entry_high = f.get("entry_high")
        bias = f.get("bias", "BUY")
        status = f.get("status", "WAITING")
        trigger_desc = f.get("trigger", "M15 Confirmation Trigger")

        # Check if price is within entry zone or touching trigger
        is_in_entry = False
        if entry_low is not None and entry_high is not None:
            low = min(float(entry_low), float(entry_high))
            high = max(float(entry_low), float(entry_high))
            if low <= float(current_price) <= high:
                is_in_entry = True

        if is_in_entry:
            last_time = LAST_ALERTED.get(pair, 0)
            if now_ts - last_time > ALERT_COOLDOWN_SECONDS:
                LAST_ALERTED[pair] = now_ts
                dir_emoji = "🟢 BUY" if bias == "BUY" else ("🔴 SELL" if bias == "SELL" else "🟡 WAIT")
                
                formatted_pair = pair
                if pair == "XAUUSD": formatted_pair = "XAU/USD (Vàng)"
                elif pair == "BTCUSD": formatted_pair = "BTC/USD (Bitcoin)"
                elif pair == "US100": formatted_pair = "US100 (Nasdaq)"
                elif len(pair) == 6: formatted_pair = f"{pair[:3]}/{pair[3:]}"

                msg = (
                    f"⚡️ *[TÙNG PHẠM ALGO LAB - CẢNH BÁO KÍCH HOẠT TRIGGER]*\n\n"
                    f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
                    f"🧭 *Hướng Kịch Bản:* *{dir_emoji}*\n"
                    f"📍 *Giá Hiện Tại:* `{current_price}` *(ĐANG CHẠM VÙNG ENTRY)*\n"
                    f"🎯 *Vùng Entry:* `{f.get('entry_zone', f'{entry_low} - {entry_high}')}`\n"
                    f"🛑 *Stop Loss (SL):* `{f.get('stop_loss', '--')}`\n"
                    f"💰 *Mục Tiêu TP:* TP1 `{f.get('tp1', '--')}` | TP2 `{f.get('tp2', '--')}`\n\n"
                    f"🔑 *Điều Kiện Kích Hoạt M15:* \n_{trigger_desc}_\n\n"
                    f"👉 *Mở Web xem xét vào lệnh ngay:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
                )

                sent = send_telegram_message(bot_token, chat_id, msg)
                if sent:
                    triggered_alerts.append({"pair": pair, "price": current_price, "time": datetime.now().strftime("%H:%M:%S")})
                    print(f"[TriggerMonitor] Successfully sent automated trigger alert for {pair} to Telegram!")

    return {
        "active": True,
        "triggered_count": len(triggered_alerts),
        "triggered_alerts": triggered_alerts
    }
