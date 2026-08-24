import os
import json
import time
import hashlib
from datetime import datetime
import threading

ANALYTICS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "analytics.json")
analytics_lock = threading.Lock()

# 100% Pure Real-time Analytics (Đếm thật 1:1)
DEFAULT_ANALYTICS = {
    "total_views": 0,
    "unique_visitors": {},
    "daily_views": {},
    "active_sessions": {}
}

def load_analytics_data() -> dict:
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Analytics] Warning reading file: {e}")
    return DEFAULT_ANALYTICS.copy()

def save_analytics_data(data: dict):
    try:
        os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Analytics] Error saving file: {e}")

def track_visitor(client_id: str = "", client_ip: str = "", is_pageview: bool = True) -> dict:
    with analytics_lock:
        data = load_analytics_data()
        now_ts = time.time()
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Hash identifier for privacy
        raw_id = f"{client_id}_{client_ip}" if client_id else (client_ip or "guest_device")
        visitor_hash = hashlib.sha256(raw_id.encode()).hexdigest()[:16]

        # 1. Update Active Session
        if "active_sessions" not in data:
            data["active_sessions"] = {}
        data["active_sessions"][visitor_hash] = now_ts

        # 2. Cleanup expired sessions (> 2 minutes inactive)
        active_cutoff = now_ts - 120
        data["active_sessions"] = {
            k: v for k, v in data["active_sessions"].items() if v > active_cutoff
        }

        # 3. Track Unique Visitor (Real Devices)
        if "unique_visitors" not in data:
            data["unique_visitors"] = {}
        if visitor_hash not in data["unique_visitors"]:
            data["unique_visitors"][visitor_hash] = today_str

        # 4. Increment Pageviews
        if is_pageview:
            data["total_views"] = data.get("total_views", 0) + 1
            if "daily_views" not in data:
                data["daily_views"] = {}
            data["daily_views"][today_str] = data["daily_views"].get(today_str, 0) + 1

        save_analytics_data(data)

        # 100% Real Exact Counts
        unique_count = len(data["unique_visitors"])
        total_views = data.get("total_views", 0)
        today_views = data.get("daily_views", {}).get(today_str, 0)
        online_now = max(1, len(data["active_sessions"]))

        return {
            "total_views": total_views,
            "unique_visitors": unique_count,
            "today_views": today_views,
            "online_now": online_now
        }

def get_analytics_stats() -> dict:
    with analytics_lock:
        data = load_analytics_data()
        now_ts = time.time()
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Cleanup expired sessions (> 2 minutes)
        active_cutoff = now_ts - 120
        active_sessions = data.get("active_sessions", {})
        active_sessions_clean = {k: v for k, v in active_sessions.items() if v > active_cutoff}
        data["active_sessions"] = active_sessions_clean

        unique_count = len(data.get("unique_visitors", {}))
        total_views = data.get("total_views", 0)
        today_views = data.get("daily_views", {}).get(today_str, 0)
        online_now = max(1, len(active_sessions_clean))

        return {
            "total_views": total_views,
            "unique_visitors": unique_count,
            "today_views": today_views,
            "online_now": online_now
        }
