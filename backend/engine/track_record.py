import os
import json
from typing import Dict, Any, List
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
TRACK_RECORD_FILE = os.path.join(DATA_DIR, "track_record.json")

# Starts empty - tracks real trades from now
INITIAL_TRACK_RECORD: List[Dict[str, Any]] = []

def load_track_record() -> List[Dict[str, Any]]:
    if os.path.exists(TRACK_RECORD_FILE):
        try:
            with open(TRACK_RECORD_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[TrackRecord] Warning reading file: {e}")
    
    save_track_record(INITIAL_TRACK_RECORD)
    return INITIAL_TRACK_RECORD

def save_track_record(records: List[Dict[str, Any]]):
    try:
        os.makedirs(os.path.dirname(TRACK_RECORD_FILE), exist_ok=True)
        with open(TRACK_RECORD_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[TrackRecord] Error saving file: {e}")

def add_track_record_entry(record: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = load_track_record()
    records.insert(0, record)
    save_track_record(records)
    return records

def delete_track_record_entry(record_id: str) -> List[Dict[str, Any]]:
    records = load_track_record()
    records = [r for r in records if r.get("id") != record_id]
    save_track_record(records)
    return records

def calculate_track_record_stats(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_setups = len(records)
    if total_setups == 0:
        return {
            "total_setups": 0,
            "wins": 0,
            "losses": 0,
            "be": 0,
            "win_rate": 0.0,
            "net_r": "+0.0R",
            "net_r_num": 0.0,
            "avg_winner": "+0.0R",
            "avg_loser": "-0.0R",
            "profit_factor": 0.0,
            "max_losing_streak": 0,
            "avg_rr": "1:2.5"
        }

    wins = [r for r in records if r.get("result") == "WIN"]
    losses = [r for r in records if r.get("result") == "LOSS"]
    be_list = [r for r in records if r.get("result") == "BE"]

    win_count = len(wins)
    loss_count = len(losses)
    be_count = len(be_list)

    # Win rate calculated over decided trades (win + loss) or total setups
    decided_trades = win_count + loss_count
    win_rate = round((win_count / decided_trades * 100), 1) if decided_trades > 0 else 0.0

    total_win_r = sum(float(r.get("r_value", 0)) for r in wins)
    total_loss_r = abs(sum(float(r.get("r_value", 0)) for r in losses))
    net_r = round(total_win_r - total_loss_r, 1)

    avg_winner = round(total_win_r / win_count, 1) if win_count > 0 else 0.0
    avg_loser = round(total_loss_r / loss_count, 1) if loss_count > 0 else 0.0
    profit_factor = round(total_win_r / total_loss_r, 2) if total_loss_r > 0 else (9.99 if total_win_r > 0 else 0.0)

    # Max losing streak calculation
    max_streak = 0
    current_streak = 0
    for r in reversed(records):
        if r.get("result") == "LOSS":
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
        elif r.get("result") == "WIN":
            current_streak = 0

    return {
        "total_setups": total_setups,
        "wins": win_count,
        "losses": loss_count,
        "be": be_count,
        "win_rate": win_rate,
        "net_r": f"+{net_r}R" if net_r > 0 else f"{net_r}R",
        "net_r_num": net_r,
        "avg_winner": f"+{avg_winner}R",
        "avg_loser": f"-{avg_loser}R",
        "profit_factor": profit_factor,
        "max_losing_streak": max_streak,
        "avg_rr": f"1:{avg_winner}" if avg_winner > 0 else "1:2.5"
    }
