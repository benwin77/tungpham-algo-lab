import os
import requests
import json
from typing import Dict, Any
from datetime import datetime

from backend.engine.track_record import add_track_record_entry

# In-memory alert cooldown tracker: { "XAUUSD_entry": timestamp, "XAUUSD_tp1": timestamp, ... }
LAST_ALERTED: Dict[str, float] = {}
ALERT_COOLDOWN_SECONDS = 1800 # 30 mins cooldown per event type

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
FORECAST_FILE = os.path.join(DATA_DIR, "forecasts.json")

DEFAULT_BOT_TOKEN = "8967574408:AAGdgUvwM8YODICgkLu5f06FZgr2SLexHcU"
DEFAULT_CHAT_ID = "344296676"

def get_telegram_credentials():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or DEFAULT_BOT_TOKEN
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip() or DEFAULT_CHAT_ID
    return token, chat

def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    token = bot_token or DEFAULT_BOT_TOKEN
    chat = chat_id or DEFAULT_CHAT_ID
    if not token or not chat:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat,
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
    bot_token, chat_id = get_telegram_credentials()

    now_ts = datetime.now().timestamp()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    triggered_alerts = []
    need_save_forecasts = False

    for pair, f in forecasts.items():
        m = market_data.get(pair, {})
        current_price_raw = m.get("current_price") or f.get("current_price")
        if current_price_raw is None:
            continue
            
        try:
            current_price = float(current_price_raw)
            entry_low = float(f.get("entry_low") or 0)
            entry_high = float(f.get("entry_high") or 0)
            sl = float(f.get("stop_loss") or 0)
            tp1 = float(f.get("tp1") or 0)
            tp2 = float(f.get("tp2") or 0)
        except Exception:
            continue

        bias = f.get("bias", "BUY")
        status = f.get("status", "WAITING")
        trigger_desc = f.get("trigger", "M15 Confirmation Trigger")
        rr_str = f.get("rr_ratio", "1:3.5")
        try:
            rr_num = float(rr_str.replace("1:", "").replace("R", "") or 3.5)
        except Exception:
            rr_num = 3.5

        formatted_pair = pair
        if pair == "XAUUSD": formatted_pair = "XAU/USD (Vàng)"
        elif pair == "BTCUSD": formatted_pair = "BTC/USD (Bitcoin)"
        elif pair == "US100": formatted_pair = "US100 (Nasdaq)"
        elif len(pair) == 6: formatted_pair = f"{pair[:3]}/{pair[3:]}"

        # -------------------------------------------------------------
        # 1. STATE: WAITING -> Check if price enters Entry Zone
        # -------------------------------------------------------------
        if status == "WAITING" and entry_low > 0 and entry_high > 0:
            low_bound = min(entry_low, entry_high)
            high_bound = max(entry_low, entry_high)
            
            if low_bound <= current_price <= high_bound:
                # Auto-transition to ACTIVE
                f["status"] = "ACTIVE"
                f["actual_entry"] = current_price
                f["activated_at"] = now_str
                need_save_forecasts = True
                
                alert_key = f"{pair}_entry"
                last_time = LAST_ALERTED.get(alert_key, 0)
                if now_ts - last_time > ALERT_COOLDOWN_SECONDS:
                    LAST_ALERTED[alert_key] = now_ts
                    dir_emoji = "🟢 BUY" if bias == "BUY" else "🔴 SELL"
                    msg = (
                        f"⚡️ *[TÙNG PHẠM ALGO LAB - LỆNH ĐÃ TỰ ĐỘNG KÍCH HOẠT]*\n\n"
                        f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
                        f"🧭 *Hướng Setup:* *{dir_emoji}*\n"
                        f"📍 *Giá Khớp Lệnh Entry:* `{current_price}` *(VÙNG CẦU/CUNG ĐÃ KHỚP)*\n"
                        f"🎯 *Vùng Entry:* `{f.get('entry_zone', f'{entry_low} - {entry_high}')}`\n"
                        f"🛑 *Stop Loss (SL):* `{sl}`\n"
                        f"💰 *Mục Tiêu TP:* TP1 `{tp1}` | TP2 `{tp2}`\n"
                        f"📈 *R:R Kỳ Vọng:* `{rr_str}`\n\n"
                        f"🔑 *Tín Hiệu Xác Nhận:* \n_{trigger_desc}_\n\n"
                        f"👉 *Theo dõi lệnh trực tiếp:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
                    )
                    send_telegram_message(bot_token, chat_id, msg)
                    triggered_alerts.append({"pair": pair, "event": "ENTRY_ACTIVE", "price": current_price})

        # -------------------------------------------------------------
        # 2. STATE: ACTIVE -> Check TP1, TP2, or SL
        # -------------------------------------------------------------
        elif status == "ACTIVE":
            actual_entry = float(f.get("actual_entry") or (entry_low + entry_high) / 2)
            
            # --- Check TP2 HIT (Full Target Win) ---
            tp2_hit = (bias == "BUY" and current_price >= tp2) or (bias == "SELL" and current_price <= tp2)
            if tp2_hit and tp2 > 0:
                f["status"] = "TP2_HIT"
                f["closed_at"] = now_str
                need_save_forecasts = True
                
                # AUTO SAVE TO JOURNAL
                pnl_pts = round(abs(current_price - actual_entry), 2)
                journal_record = {
                    "id": f"rec_{pair}_{int(now_ts)}",
                    "pair": pair,
                    "type": bias,
                    "entry_price": actual_entry,
                    "exit_price": current_price,
                    "pnl_pips": f"+{pnl_pts} pts",
                    "r_value": rr_num,
                    "result": "WIN",
                    "status_badge": "TP2 HIT 🎯",
                    "date": now_str,
                    "notes": f"Hệ thống tự động chốt lời toàn phần TP2 ({current_price}) theo cấu trúc Liquidity Target."
                }
                add_track_record_entry(journal_record)
                
                alert_key = f"{pair}_tp2"
                LAST_ALERTED[alert_key] = now_ts
                msg = (
                    f"🏆 *[TÙNG PHẠM ALGO LAB - CHỐT LỜI TP2 TOÀN PHẦN 🎯]*\n\n"
                    f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
                    f"🧭 *Lệnh:* *{bias}* | Giá Khớp TP2: `{current_price}`\n"
                    f"💵 *Lợi Nhuận Thu Về:* `+{pnl_pts} pts` • *+{rr_num}R*\n\n"
                    f"✅ *Hệ thống đã TỰ ĐỘNG ghi nhận vào Tab [Nhật Ký Lệnh] & cập nhật Winrate!*\n"
                    f"👉 *Xem bảng thống kê:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
                )
                send_telegram_message(bot_token, chat_id, msg)
                triggered_alerts.append({"pair": pair, "event": "TP2_HIT", "price": current_price})

            # --- Check TP1 HIT (Partial / Breakeven SL) ---
            elif (bias == "BUY" and current_price >= tp1) or (bias == "SELL" and current_price <= tp1):
                alert_key = f"{pair}_tp1"
                last_time = LAST_ALERTED.get(alert_key, 0)
                if now_ts - last_time > ALERT_COOLDOWN_SECONDS:
                    LAST_ALERTED[alert_key] = now_ts
                    f["status"] = "TP1_HIT"
                    need_save_forecasts = True
                    pnl_pts = round(abs(current_price - actual_entry), 2)
                    msg = (
                        f"🎯 *[TÙNG PHẠM ALGO LAB - ĐẠT MỤC TIÊU TP1]*\n\n"
                        f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
                        f"🧭 *Lệnh:* *{bias}* | Giá Hiện Tại: `{current_price}`\n"
                        f"💰 *Lợi Nhuận TP1:* `+{pnl_pts} pts` *(+1.5R)*\n"
                        f"🛡 *Khuyến Nghị:* Khóa 50% khối lượng và dời Stop Loss về vùng Entry `{actual_entry}` an toàn tuyệt đối!\n\n"
                        f"👉 *Mở Web:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
                    )
                    send_telegram_message(bot_token, chat_id, msg)
                    triggered_alerts.append({"pair": pair, "event": "TP1_HIT", "price": current_price})

            # --- Check STOP LOSS HIT ---
            elif (bias == "BUY" and current_price <= sl) or (bias == "SELL" and current_price >= sl):
                f["status"] = "INVALIDATED"
                f["closed_at"] = now_str
                need_save_forecasts = True
                
                # AUTO SAVE LOSS TO JOURNAL
                loss_pts = round(abs(actual_entry - current_price), 2)
                journal_record = {
                    "id": f"rec_{pair}_{int(now_ts)}",
                    "pair": pair,
                    "type": bias,
                    "entry_price": actual_entry,
                    "exit_price": current_price,
                    "pnl_pips": f"-{loss_pts} pts",
                    "r_value": -1.0,
                    "result": "LOSS",
                    "status_badge": "SL HIT 🛑",
                    "date": now_str,
                    "notes": f"Lệnh chạm mức cắt lỗ Stop Loss ({current_price}) theo ATR H4 bảo vệ an toàn vốn."
                }
                add_track_record_entry(journal_record)
                
                alert_key = f"{pair}_sl"
                LAST_ALERTED[alert_key] = now_ts
                msg = (
                    f"🛑 *[TÙNG PHẠM ALGO LAB - CHẠM STOP LOSS]*\n\n"
                    f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
                    f"🧭 *Lệnh:* *{bias}* | Giá Cắt Lỗ: `{current_price}`\n"
                    f"🛡 *Rủi Ro Đã Chặn:* `-1.0R` (`-{loss_pts} pts`)\n\n"
                    f"✅ *Hệ thống đã TỰ ĐỘNG ghi nhận vào Tab [Nhật Ký Lệnh] để thống kê kỷ luật.*\n"
                    f"👉 *Xem chi tiết:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
                )
                send_telegram_message(bot_token, chat_id, msg)
                triggered_alerts.append({"pair": pair, "event": "SL_HIT", "price": current_price})

    if need_save_forecasts:
        try:
            with open(FORECAST_FILE, "w", encoding="utf-8") as f_out:
                json.dump(forecasts, f_out, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TriggerMonitor] Error saving updated forecast state: {e}")

    return {
        "active": True,
        "triggered_count": len(triggered_alerts),
        "triggered_alerts": triggered_alerts
    }

def send_manual_update_telegram_alert(pair: str, f: Dict[str, Any], old_status: str = "") -> bool:
    bot_token, chat_id = get_telegram_credentials()
    if not bot_token or not chat_id:
        return False
        
    bias = f.get("bias", "BUY")
    status = f.get("status", "ACTIVE")
    formatted_pair = pair
    if pair == "XAUUSD": formatted_pair = "XAU/USD (Vàng)"
    elif pair == "BTCUSD": formatted_pair = "BTC/USD (Bitcoin)"
    elif pair == "US100": formatted_pair = "US100 (Nasdaq)"
    elif len(pair) == 6: formatted_pair = f"{pair[:3]}/{pair[3:]}"
    
    dir_emoji = "🟢 BUY" if bias == "BUY" else "🔴 SELL"
    status_icon = "⚡️ ĐANG CHẠY LỆNH (ACTIVE)" if status == "ACTIVE" else (
        "🎯 ĐÃ ĐẠT TP1" if status == "TP1_HIT" else (
            "🏆 ĐÃ CHỐT TP2" if status == "TP2_HIT" else (
                "🛑 DỪNG LỖ / HỦY" if status == "INVALIDATED" else "🟡 ĐANG CANH (WAITING)"
            )
        )
    )

    msg = (
        f"📣 *[TÙNG PHẠM ALGO LAB - CẬP NHẬT TRẠNG THÁI SETUP]*\n\n"
        f"📊 *Cặp Tài Sản:* #{pair} • {formatted_pair}\n"
        f"🧭 *Hướng Setup:* *{dir_emoji}*\n"
        f"📌 *Trạng Thái:* *{status_icon}*\n"
        f"🎯 *Vùng Entry:* `{f.get('entry_zone', '--')}`\n"
        f"🛑 *Stop Loss (SL):* `{f.get('stop_loss', '--')}`\n"
        f"💰 *Take Profit:* TP1 `{f.get('tp1', '--')}` | TP2 `{f.get('tp2', '--')}`\n"
        f"📈 *Tỷ Lệ R:R:* `{f.get('rr_ratio', '1:3.5')}`\n\n"
        f"👉 *Xem chi tiết trên Terminal:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
    )
    return send_telegram_message(bot_token, chat_id, msg)
