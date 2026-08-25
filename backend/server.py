from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import uvicorn
import hashlib
from datetime import datetime

from backend.collectors.calendar_collector import get_weekly_calendar
from backend.collectors.price_collector import get_all_pairs_technical, get_asset_technical_data, fetch_tradingview_spot_data
from backend.collectors.news_collector import fetch_latest_news, get_pair_sentiment_summary
from backend.engine.smc_analyzer import build_all_weekly_forecasts, generate_smc_setup
from backend.engine.analytics import track_visitor, get_analytics_stats
from backend.engine.track_record import load_track_record, calculate_track_record_stats, save_track_record
from backend.engine.quant_lab import load_quant_lab_data
from backend.engine.trigger_monitor import check_and_send_trigger_alerts, send_telegram_message

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "tungpham8888")
ADMIN_TOKEN = f"tp_auth_{hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest()[:18]}"

app = FastAPI(title="TÙNG PHẠM ALGO LAB - SMC & PA Weekly Trading Terminal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def is_admin_authorized(request: Request) -> bool:
    token = request.headers.get("X-Admin-Token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    return token == ADMIN_TOKEN

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
FORECAST_FILE = os.path.join(DATA_DIR, "forecasts.json")
CACHE_FILE = os.path.join(DATA_DIR, "cache.json")

os.makedirs(DATA_DIR, exist_ok=True)

# In-memory cache for speed
APP_STATE = {
    "tech_data": {},
    "news": [],
    "calendar": [],
    "forecasts": {},
    "last_updated": ""
}

def refresh_all_data():
    global APP_STATE
    try:
        print("[Backend] Refreshing prices, calendar, news...")
        calendar_events = get_weekly_calendar()
        news_items = fetch_latest_news()
        tech_data = get_all_pairs_technical()
        
        forecasts = build_all_weekly_forecasts(tech_data, news_items, calendar_events, FORECAST_FILE)
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for k in forecasts:
            if not forecasts[k].get("updated_at"):
                forecasts[k]["updated_at"] = now_str
                
        APP_STATE["calendar"] = calendar_events
        APP_STATE["news"] = news_items
        APP_STATE["tech_data"] = tech_data
        APP_STATE["forecasts"] = forecasts
        APP_STATE["last_updated"] = now_str
        
        # Save to disk
        with open(FORECAST_FILE, "w", encoding="utf-8") as f:
            json.dump(forecasts, f, ensure_ascii=False, indent=2)
            
        print("[Backend] Data refresh completed successfully!")
    except Exception as e:
        print(f"[Backend] Error during data refresh: {e}")

# Initial Load
refresh_all_data()

# Background Scheduler (Guarantees fresh Sunday analysis for Monday trading)
import threading
import time

def background_weekly_scheduler():
    while True:
        try:
            time.sleep(4 * 3600)  # Every 4 hours auto-sync
            print("[Scheduler] Running automatic background weekly data & calendar sync...")
            refresh_all_data()
        except Exception as e:
            print(f"[Scheduler] Background worker notice: {e}")

def background_price_streamer():
    """
    Constantly updates real-time prices for all 6 pairs in memory every 5 seconds.
    """
    while True:
        try:
            time.sleep(5)
            fresh_spot = fetch_tradingview_spot_data()
            if fresh_spot:
                for p, d in fresh_spot.items():
                    if p not in APP_STATE["tech_data"]:
                        APP_STATE["tech_data"][p] = {}
                    APP_STATE["tech_data"][p].update(d)
                    
                    # Also sync price into active forecasts
                    if p in APP_STATE.get("forecasts", {}):
                        APP_STATE["forecasts"][p]["current_price"] = d.get("current_price", APP_STATE["forecasts"][p].get("current_price"))
                
                # Check real-time trigger and send Telegram alert if entry zone hit
                check_and_send_trigger_alerts(APP_STATE["tech_data"], APP_STATE["forecasts"])
        except Exception as e:
            pass

scheduler_thread = threading.Thread(target=background_weekly_scheduler, daemon=True)
scheduler_thread.start()

price_stream_thread = threading.Thread(target=background_price_streamer, daemon=True)
price_stream_thread.start()

# Data models for updating scenarios
class CheckItem(BaseModel):
    text: str
    checked: bool

class LoginRequest(BaseModel):
    password: str

class ForecastUpdateRequest(BaseModel):
    pair: str
    bias: str
    bias_badge: Optional[str] = None
    status: Optional[str] = "PLANNING"
    entry_zone: Optional[str] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    rr_ratio: Optional[str] = None
    trigger: Optional[str] = None
    rationale: Optional[str] = None
    user_notes: Optional[str] = None
    checklist: Optional[List[CheckItem]] = None

class AnalyticsTrackRequest(BaseModel):
    client_id: Optional[str] = ""
    is_pageview: Optional[bool] = True

@app.post("/api/analytics/track")
def api_track_visitor(req: AnalyticsTrackRequest, request: Request):
    client_ip = request.client.host if request.client else ""
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    stats = track_visitor(client_id=req.client_id, client_ip=client_ip, is_pageview=req.is_pageview)
    return stats

@app.get("/api/analytics/stats")
def api_get_analytics():
    return get_analytics_stats()

class TrackRecordAddRequest(BaseModel):
    pair: str
    direction: str
    strategy: str
    entry: str
    sl: str
    tp: str
    r_multiple: str
    r_value: float
    result: str # WIN / LOSS / BE
    notes: Optional[str] = ""

class TelegramAlertRequest(BaseModel):
    pair: str
    direction: str
    status: str
    entry: str
    sl: str
    tp1: str
    tp2: str
    trigger: str

@app.get("/api/track-record")
def get_track_record():
    records = load_track_record()
    stats = calculate_track_record_stats(records)
    return {
        "stats": stats,
        "records": records
    }

@app.post("/api/track-record/add")
def add_track_record(req: TrackRecordAddRequest, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin để thêm lịch sử lệnh!")
    records = load_track_record()
    new_record = {
        "id": f"tr_{int(datetime.now().timestamp())}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "pair": req.pair,
        "direction": req.direction,
        "strategy": req.strategy,
        "entry": req.entry,
        "sl": req.sl,
        "tp": req.tp,
        "r_multiple": req.r_multiple,
        "r_value": req.r_value,
        "result": req.result,
        "status_label": f"✅ TP Hit ({req.r_multiple})" if req.result == "WIN" else (f"❌ Hit SL ({req.r_multiple})" if req.result == "LOSS" else "⏸️ Breakeven"),
        "notes": req.notes
    }
    records.insert(0, new_record)
    save_track_record(records)
    return {"success": True, "record": new_record, "stats": calculate_track_record_stats(records)}

@app.delete("/api/track-record/{record_id}")
def delete_track_record(record_id: str, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin để xóa lệnh khỏi nhật ký!")
    records = delete_track_record_entry(record_id)
    return {"success": True, "stats": calculate_track_record_stats(records)}

@app.get("/api/quant-lab")
def get_quant_lab():
    strategies = load_quant_lab_data()
    return {
        "lab_name": "TÙNG PHẠM QUANT LAB",
        "description": "Báo cáo nghiên cứu chiến lược định lượng & Backtest thực chiến (2019 – 2026)",
        "strategies": strategies
    }

@app.post("/api/alerts/telegram")
def trigger_telegram_alert(req: TelegramAlertRequest, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin để phát cảnh báo!")
    
    # Format PRO alert message
    alert_msg = (
        f"🚨 [TÙNG PHẠM ALGO LAB - SETUP ACTIVE]\n"
        f"📊 Cặp: #{req.pair} ({req.direction})\n"
        f"⚡️ Trạng thái: {req.status}\n"
        f"🎯 Vùng Entry: {req.entry}\n"
        f"🛑 Dừng lỗ (SL): {req.sl}\n"
        f"💰 Chốt lời TP1: {req.tp1} | TP2: {req.tp2}\n"
        f"🔑 Trigger: {req.trigger}\n"
        f"------------------------------------\n"
        f"👉 Trade the plan. Not the noise."
    )
    
    # If TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID exist in env, send to Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    sent = False
    if bot_token and chat_id:
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": alert_msg, "parse_mode": "Markdown"}, timeout=5)
            sent = True
        except Exception as e:
            print(f"[Telegram Alert] Error sending: {e}")
            
    return {
        "success": True,
        "message": "Đã phát cảnh báo kịch bản thành công!",
        "alert_text": alert_msg,
        "sent_telegram": sent
    }

class TelegramConfigRequest(BaseModel):
    bot_token: Optional[str] = ""
    chat_id: Optional[str] = ""

@app.post("/api/alerts/test-telegram")
def test_telegram_alert(req: TelegramConfigRequest, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin để gửi test cảnh báo!")
    
    bot_token = req.bot_token.strip() if req.bot_token else os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = req.chat_id.strip() if req.chat_id else os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        return {
            "success": False,
            "message": "Chưa có TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID. Vui lòng cung cấp Bot Token và Chat ID!"
        }

    test_msg = (
        "🚀 *[TÙNG PHẠM ALGO LAB - KẾT NỐI TELEGRAM THÀNH CÔNG]*\n\n"
        "✅ Xin chào anh Tùng! Hệ thống cảnh báo tự động khi giá chạm Entry & kích hoạt M15 Trigger đã sẵn sàng hoạt động 24/7.\n\n"
        "👉 *Xem Terminal:* [Tùng Phạm Algo Lab](https://tungpham-algo-lab.onrender.com)"
    )

    sent = send_telegram_message(bot_token, chat_id, test_msg)
    return {
        "success": sent,
        "message": "Đã gửi tin nhắn thử nghiệm thành công tới Telegram của Mr Tung!" if sent else "Gửi thất bại, vui lòng kiểm tra lại Bot Token và Chat ID (đảm bảo anh đã bấm /start với bot)."
    }

@app.post("/api/auth/login")
def admin_login(req: LoginRequest):
    if req.password == ADMIN_PASSWORD:
        return {
            "success": True,
            "token": ADMIN_TOKEN,
            "admin_name": "Mr Tung",
            "message": "Đăng nhập quyền Admin thành công!"
        }
    raise HTTPException(status_code=401, detail="Mật khẩu Admin không chính xác!")

@app.get("/api/auth/verify")
def verify_auth(request: Request):
    is_auth = is_admin_authorized(request)
    return {
        "authenticated": is_auth,
        "admin_name": "Mr Tung" if is_auth else None
    }

@app.get("/api/health")
def get_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "tungpham-algo-lab"
    }

@app.get("/api/status")
def get_status():
    return {
        "status": "online",
        "last_updated": APP_STATE.get("last_updated"),
        "pairs_count": len(APP_STATE.get("forecasts", {})),
        "news_count": len(APP_STATE.get("news", [])),
        "calendar_count": len(APP_STATE.get("calendar", []))
    }

@app.get("/api/market-data")
def get_market_data():
    return APP_STATE.get("tech_data", {})

@app.get("/api/forecasts")
def get_forecasts():
    # Read fresh from file if exists
    if os.path.exists(FORECAST_FILE):
        try:
            with open(FORECAST_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                APP_STATE["forecasts"] = saved
        except Exception:
            pass
    return APP_STATE.get("forecasts", {})

@app.post("/api/forecasts/update")
def update_forecast(req: ForecastUpdateRequest, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin (Mr Tung) để lưu kịch bản!")
        
    pair = req.pair
    if pair not in APP_STATE.get("forecasts", {}):
        raise HTTPException(status_code=404, detail="Pair not found")
        
    current = APP_STATE["forecasts"][pair]
    
    # Update fields
    current["bias"] = req.bias
    if req.bias_badge:
        current["bias_badge"] = req.bias_badge
    else:
        current["bias_badge"] = f"🟢 {req.bias} (User Custom Setup)" if req.bias == "BUY" else f"🔴 {req.bias} (User Custom Setup)"
        
    if req.status:
        current["status"] = req.status
    if req.entry_zone is not None:
        current["entry_zone"] = req.entry_zone
    if req.stop_loss is not None:
        current["stop_loss"] = req.stop_loss
    if req.tp1 is not None:
        current["tp1"] = req.tp1
    if req.tp2 is not None:
        current["tp2"] = req.tp2
    if req.rr_ratio is not None:
        current["rr_ratio"] = req.rr_ratio
    if req.trigger is not None:
        current["trigger"] = req.trigger
    if req.rationale is not None:
        current["rationale"] = req.rationale
    if req.user_notes is not None:
        current["user_notes"] = req.user_notes
    if req.checklist is not None:
        current["checklist"] = [item.dict() for item in req.checklist]
        
    current["user_customized"] = True
    current["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save to disk
    with open(FORECAST_FILE, "w", encoding="utf-8") as f:
        json.dump(APP_STATE["forecasts"], f, ensure_ascii=False, indent=2)
        
    return {"message": "Updated successfully", "pair": pair, "forecast": current}

@app.post("/api/forecasts/reset/{pair}")
def reset_forecast(pair: str, request: Request):
    if not is_admin_authorized(request):
        raise HTTPException(status_code=401, detail="Yêu cầu quyền Admin (Mr Tung) để khôi phục kịch bản!")
        
    if pair not in APP_STATE.get("tech_data", {}):
        raise HTTPException(status_code=404, detail="Pair not found")
        
    tech = APP_STATE["tech_data"][pair]
    sent = get_pair_sentiment_summary(pair, APP_STATE["news"])
    auto_setup = generate_smc_setup(pair, tech, sent, APP_STATE["calendar"])
    auto_setup["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    auto_setup["user_customized"] = False
    
    APP_STATE["forecasts"][pair] = auto_setup
    
    with open(FORECAST_FILE, "w", encoding="utf-8") as f:
        json.dump(APP_STATE["forecasts"], f, ensure_ascii=False, indent=2)
        
    return {"message": f"Reset {pair} to auto-SMC forecast", "forecast": auto_setup}

@app.get("/api/calendar")
def get_calendar(currency: Optional[str] = None, impact: Optional[str] = None):
    events = APP_STATE.get("calendar", [])
    if currency and currency != "ALL":
        events = [e for e in events if e.get("currency") == currency]
    if impact and impact != "ALL":
        events = [e for e in events if e.get("impact", "").lower() == impact.lower()]
    return events

@app.get("/api/news")
def get_news(pair: Optional[str] = None):
    news_items = APP_STATE.get("news", [])
    if pair and pair != "ALL":
        news_items = [n for n in news_items if pair in n.get("pairs", []) or "ALL" in n.get("pairs", [])]
    return news_items

@app.post("/api/refresh")
def force_refresh():
    refresh_all_data()
    return {"message": "Data refreshed successfully", "last_updated": APP_STATE.get("last_updated")}

@app.get("/api/export-text")
def export_text_summary():
    """
    Format the complete weekly trading setups into an elegant markdown / text summary for Telegram or copy-paste.
    """
    lines = []
    lines.append(f"⚡️ TÙNG PHẠM ALGO LAB - SMC & PA WEEKLY INTELLIGENCE")
    lines.append(f"🎯 Minimal • Precision • Gold Index Strategy")
    lines.append(f"📊 KỊCH BẢN GIAO DỊCH ĐẦU TUẦN (SMC + PURE PRICE ACTION + TREND)")
    lines.append(f"⏰ Thời gian cập nhật: {APP_STATE.get('last_updated', datetime.now().strftime('%Y-%m-%d %H:%M'))}\n")
    lines.append("="*48)
    
    for pair, f_data in APP_STATE.get("forecasts", {}).items():
        bias_icon = "🟢" if f_data.get("bias") == "BUY" else ("🔴" if f_data.get("bias") == "SELL" else "⚪️")
        lines.append(f"\n{bias_icon} **{pair} ({f_data.get('name')})** - [{f_data.get('status')}]")
        lines.append(f"• Xu Hướng/Bias: {f_data.get('bias_badge')}")
        lines.append(f"• Vùng Entry: {f_data.get('entry_zone')}")
        lines.append(f"• Stop Loss (SL): {f_data.get('stop_loss')}")
        lines.append(f"• Target TP1: {f_data.get('tp1')} | TP2: {f_data.get('tp2')} (R:R {f_data.get('rr_ratio')})")
        lines.append(f"• Vùng Order Block: {f_data.get('ob_zone')}")
        lines.append(f"• Cản Key S/R: {f_data.get('key_sr')}")
        lines.append(f"• Kế hoạch: {f_data.get('rationale')}")
        if f_data.get("user_notes"):
            lines.append(f"• Ghi chú riêng: {f_data.get('user_notes')}")
        lines.append("-" * 40)
        
    lines.append("\n📞 Hotline / Zalo: 0903.663.060 (Tung Pham)")
    lines.append("© Tùng Phạm Algo Lab • Trade With Discipline & Risk Management")
    return {"text": "\n".join(lines)}

# Mount static frontend directory
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend index.html not found"}

if __name__ == "__main__":
    uvicorn.run("backend.server:app", host="127.0.0.1", port=8000, reload=True)
