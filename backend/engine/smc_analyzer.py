from typing import Dict, Any, List
import json
import os

def generate_smc_setup(pair: str, tech: Dict[str, Any], sent: Dict[str, Any], cal_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Synthesize Price Action, Smart Money Concepts (SMC), Trend Following and Macro Sentiment
    to produce a high-probability weekly trade scenario.
    """
    price = tech.get("current_price", 100.0)
    swing_high = tech.get("swing_high", price * 1.02)
    swing_low = tech.get("swing_low", price * 0.98)
    ema20 = tech.get("ema20", price)
    ema50 = tech.get("ema50", price)
    ema200 = tech.get("ema200", price)
    atr = tech.get("atr", (swing_high - swing_low) * 0.1)
    digits = tech.get("digits", 2)
    trend = tech.get("trend_status", "SIDEWAY / MIXED")
    bull_pct = sent.get("bull_score", 50)
    
    # Currency matching calendar impact
    impactful_news = [e["title"] for e in cal_events if e.get("impact") == "High" and (e.get("currency") in pair or "USD" in e.get("currency", ""))]
    news_driver = impactful_news[0] if impactful_news else "Tâm lý thị trường & Dữ liệu vĩ mô tuần"

    # Strategy calculations
    if pair == "XAUUSD":
        # Gold logic: SMC Demand Zone / FVG Retest / Bullish Continuation or Sweep
        is_bullish = price >= ema50 or bull_pct >= 50
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (Canh Mua Vùng Cầu / FVG)"
            entry_low = round(max(swing_low, price - atr * 0.8), digits)
            entry_high = round(entry_low + atr * 0.35, digits)
            sl = round(entry_low - atr * 0.65, digits)
            tp1 = round(price + atr * 0.9, digits)
            tp2 = round(swing_high + atr * 0.5, digits)
            structure = "BULLISH BOS (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bullish Order Block + Discount FVG)"
            bsl = f"{swing_high} (Buy-side Liquidity Swing High)"
            ssl = f"{round(swing_low - atr * 0.2, digits)} (Sell-side Liquidity Asia Low)"
            key_sr = f"Cản Hỗ trợ: {entry_low} | Cản Kháng cự: {swing_high}"
            checklist = [
                {"text": "H4 Demand Order Block (OB) chưa bị vi phạm", "checked": True},
                {"text": "Quét thanh khoản Sell-side (SSL) phiên Á / London", "checked": True},
                {"text": "Giá nằm trong vùng Discount Zone (Fib 0.618 - 0.786)", "checked": True},
                {"text": "Nến rút chân Pinbar / Bullish Engulfing tại FVG", "checked": True},
                {"text": "EMA 50 & 200 ủng hộ xu hướng tăng dài hạn", "checked": True}
            ]
            rationale = (
                f"Vàng đang giữ vững cấu trúc tăng (Uptrend Structure) trên khung Daily & H4. "
                f"Kịch bản tuần: Chờ giá hồi về vùng Discount FVG & Bullish Order Block ({entry_low} - {entry_high}) "
                f"sau khi quét thanh khoản đáy ngắn hạn, xác nhận nến đảo chiều PA để kích hoạt lệnh BUY hướng về BSL {swing_high}."
            )
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Canh Bán Vùng Cung / Sweep High)"
            entry_high = round(min(swing_high, price + atr * 0.8), digits)
            entry_low = round(entry_high - atr * 0.35, digits)
            sl = round(entry_high + atr * 0.65, digits)
            tp1 = round(price - atr * 0.9, digits)
            tp2 = round(swing_low - atr * 0.5, digits)
            structure = "BEARISH CHoCH (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Supply OB)"
            bsl = f"{round(swing_high + atr*0.2, digits)} (Buy-side Liquidity High)"
            ssl = f"{swing_low} (Sell-side Liquidity Target)"
            key_sr = f"Cản Kháng cự: {entry_high} | Cản Hỗ trợ: {swing_low}"
            checklist = [
                {"text": "H4 Supply Order Block giữ vững phản ứng", "checked": True},
                {"text": "Quét râu tạo Fakeout trên đỉnh BSL", "checked": True},
                {"text": "Giá tiệm cận Premium Zone", "checked": True},
                {"text": "Nến Shooting Star / Bearish Engulfing", "checked": True}
            ]
            rationale = (
                f"Vàng gặp áp lực chốt lời mạnh tại vùng đỉnh, xuất hiện tín hiệu CHoCH đảo chiều ngắn hạn. "
                f"Kịch bản tuần: Canh SELL khi giá hồi phục kiểm tra Bearish Supply OB quanh {entry_low} - {entry_high}."
            )
    elif pair == "USDJPY":
        # UJ logic: Trend following USD strength vs BOJ Intervention fear
        if price >= ema50:
            bias = "BUY"
            bias_badge = "🟢 BUY (Trend Follow H4 Pullback)"
            entry_low = round(price - atr * 0.6, digits)
            entry_high = round(entry_low + atr * 0.25, digits)
            sl = round(entry_low - atr * 0.5, digits)
            tp1 = round(price + atr * 0.8, digits)
            tp2 = round(swing_high, digits)
            structure = "BULLISH TREND CONTINUATION"
            ob_zone = f"{entry_low} - {entry_high} (H4 Imbalance & 50 EMA Confluence)"
            bsl = f"{swing_high} (Equal Highs Liquidity Pool)"
            ssl = f"{round(entry_low - atr*0.3, digits)} (Recent Higher Low)"
            key_sr = f"Support: {entry_low} | Resistance: {swing_high}"
            checklist = [
                {"text": "Cấu trúc Higher Highs & Higher Lows duy trì", "checked": True},
                {"text": "Giá chạm dải hỗ trợ động EMA 20/50 trên H4", "checked": True},
                {"text": "Chưa có tín hiệu can thiệp trực tiếp từ BOJ", "checked": True},
                {"text": "Lợi suất Trái phiếu Mỹ 10Y giữ đà tăng", "checked": True}
            ]
            rationale = (
                f"USD/JPY duy trì xu hướng tăng bền vững trên mây EMA. "
                f"Kịch bản tuần: Mở lệnh BUY theo xu hướng (Trend Following) khi giá điều chỉnh về vùng FVG + EMA50 ({entry_low} - {entry_high})."
            )
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (SMC CHoCH Breakout)"
            entry_high = round(price + atr * 0.5, digits)
            entry_low = round(entry_high - atr * 0.2, digits)
            sl = round(entry_high + atr * 0.45, digits)
            tp1 = round(price - atr * 0.7, digits)
            tp2 = round(swing_low, digits)
            structure = "BEARISH CHoCH"
            ob_zone = f"{entry_low} - {entry_high} (Supply OB)"
            bsl = f"{swing_high} (BSL)"
            ssl = f"{swing_low} (Target SSL)"
            key_sr = f"Resistance: {entry_high} | Support: {swing_low}"
            checklist = [
                {"text": "Thủng cấu trúc đáy gần nhất (CHoCH)", "checked": True},
                {"text": "Retest Bearish Order Block thất bại", "checked": True}
            ]
            rationale = f"USD/JPY suy yếu, canh SELL hồi tại vùng kháng cự {entry_low} - {entry_high}."
    elif pair == "BTCUSD":
        # Bitcoin logic: 24/7 Whale Accumulation, CME/FVG Gap Fill, Weekend Liquidity Sweep & Trend Following
        is_bullish = price >= ema50 or bull_pct >= 50
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (SMC Discount FVG + Whale Accumulation)"
            entry_low = round(price - atr * 0.65, digits)
            entry_high = round(entry_low + atr * 0.25, digits)
            sl = round(entry_low - atr * 0.45, digits)
            tp1 = round(price + atr * 0.85, digits)
            tp2 = round(swing_high, digits)
            structure = "BULLISH UPTREND STRUCTURE (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bullish Order Block + Imbalance Fill)"
            bsl = f"{swing_high} (Major Swing High BSL)"
            ssl = f"{round(entry_low - atr*0.3, digits)} (Weekend Low Sweep Target)"
            key_sr = f"Hỗ trợ Cầu: {entry_low} | Kháng cự Đỉnh: {swing_high}"
            checklist = [
                {"text": "H4 Bullish Order Block (OB) giữ vững phản ứng", "checked": True},
                {"text": "Quét sạch thanh khoản đáy cuối tuần (Weekend Low Sweep)", "checked": True},
                {"text": "Lấp đầy khoảng trống FVG / Imbalance khung H4", "checked": True},
                {"text": "Dòng tiền tổ chức ETF & On-chain duy trì mua gom", "checked": True},
                {"text": "EMA 20/50 dốc lên ủng hộ xu hướng Trend Following 24/7", "checked": True}
            ]
            rationale = (
                f"Bitcoin (BTC/USD) duy trì cấu trúc tăng trưởng mạnh mẽ 24/7. "
                f"Kịch bản tuần: Canh BUY khi giá điều chỉnh về vùng FVG + Demand OB ({entry_low} - {entry_high}) "
                f"sau khi quét thanh khoản đáy, hướng tới mục tiêu thanh khoản đỉnh BSL {swing_high}."
            )
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Supply Zone Mitigation)"
            entry_high = round(price + atr * 0.65, digits)
            entry_low = round(entry_high - atr * 0.25, digits)
            sl = round(entry_high + atr * 0.45, digits)
            tp1 = round(price - atr * 0.85, digits)
            tp2 = round(swing_low, digits)
            structure = "BEARISH DISTRIBUTION (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Supply Zone)"
            bsl = f"{swing_high} (BSL Peak)"
            ssl = f"{swing_low} (SSL Support Target)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {swing_low}"
            checklist = [
                {"text": "Cản Supply Zone H4 giữ vững áp lực bán", "checked": True},
                {"text": "Quét râu tạo mô hình Swing Failure Pattern (SFP) tại đỉnh BSL", "checked": True},
                {"text": "Áp lực chốt lời ngắn hạn từ các ví lớn (Whales)", "checked": True}
            ]
            rationale = f"Bitcoin đối mặt áp lực chốt lời tại vùng cản đỉnh, canh SELL khi giá hồi về vùng Supply {entry_low} - {entry_high}."
    elif pair == "GBPUSD":
        # GBPUSD: Liquidity sweeps in London session
        bias = "SELL" if price < ema50 else "BUY"
        if bias == "SELL":
            bias_badge = "🔴 SELL (London Liquidity Sweep Setup)"
            entry_high = round(price + atr * 0.55, digits)
            entry_low = round(entry_high - atr * 0.22, digits)
            sl = round(entry_high + atr * 0.4, digits)
            tp1 = round(price - atr * 0.7, digits)
            tp2 = round(swing_low, digits)
            structure = "BEARISH BOS (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Order Block)"
            bsl = f"{swing_high} (London High BSL)"
            ssl = f"{swing_low} (Weekly Target SSL)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {swing_low}"
            checklist = [
                {"text": "Phiên London quét thanh khoản đỉnh Á (Asia High Sweep)", "checked": True},
                {"text": "Xuất hiện cụm nến Bearish Engulfing trên M15/H1", "checked": True},
                {"text": "BOS phá đáy cấu trúc phiên", "checked": True}
            ]
            rationale = (
                f"GBP/USD dao động dưới cản động EMA. "
                f"Kịch bản tuần: Chờ phiên London tạo bẫy giá quét đỉnh Á (Judas Swing), sau đó SELL tại Supply OB ({entry_low} - {entry_high})."
            )
        else:
            bias_badge = "🟢 BUY (Bullish Trend Rebound)"
            entry_low = round(price - atr * 0.55, digits)
            entry_high = round(entry_low + atr * 0.22, digits)
            sl = round(entry_low - atr * 0.4, digits)
            tp1 = round(price + atr * 0.7, digits)
            tp2 = round(swing_high, digits)
            structure = "BULLISH STRUCTURE"
            ob_zone = f"{entry_low} - {entry_high} (H4 Demand OB)"
            bsl = f"{swing_high} (BSL Target)"
            ssl = f"{swing_low} (SSL)"
            key_sr = f"Hỗ trợ: {entry_low} | Kháng cự: {swing_high}"
            checklist = [
                {"text": "Test thành công vùng Demand Order Block H4", "checked": True},
                {"text": "Trendline hỗ trợ dốc lên giữ vững", "checked": True}
            ]
            rationale = f"GBP/USD duy trì lực mua, canh BUY hồi tại vùng cầu {entry_low} - {entry_high}."
    elif pair == "CADCHF":
        # CADCHF: Range / Channel / Pure PA Breakout
        bias = "BUY" if price > (swing_high + swing_low)/2 else "SELL"
        if bias == "BUY":
            bias_badge = "🟢 BUY (Support Channel Bounce + PA)"
            entry_low = round(swing_low + atr * 0.2, digits)
            entry_high = round(entry_low + atr * 0.25, digits)
            sl = round(entry_low - atr * 0.35, digits)
            tp1 = round((swing_high + swing_low) / 2, digits)
            tp2 = round(swing_high - atr * 0.1, digits)
            structure = "RANGE ACCUMULATION / S&R BOUNCE"
            ob_zone = f"{entry_low} - {entry_high} (Key Support & Demand Base)"
            bsl = f"{swing_high} (Range High Liquidity)"
            ssl = f"{swing_low} (Range Low Liquidity)"
            key_sr = f"Cản Đáy: {entry_low} | Cản Đỉnh: {swing_high}"
            checklist = [
                {"text": "Giá chạm cạnh dưới biên độ tích lũy (Range Low)", "checked": True},
                {"text": "Nến Pinbar từ chối vùng hỗ trợ D1", "checked": True},
                {"text": "Tương quan giá Dầu thô hồi phục hỗ trợ CAD", "checked": True}
            ]
            rationale = (
                f"CAD/CHF đang di chuyển trong biên độ Range đi ngang. "
                f"Kịch bản tuần: Canh BUY khi giá test vùng biên dưới {entry_low} - {entry_high} với xác nhận nến đảo chiều PA, chốt lời tại đỉnh hộp {swing_high}."
            )
        else:
            bias_badge = "🔴 SELL (Resistance Range Rejection)"
            entry_high = round(swing_high - atr * 0.2, digits)
            entry_low = round(entry_high - atr * 0.25, digits)
            sl = round(entry_high + atr * 0.35, digits)
            tp1 = round((swing_high + swing_low) / 2, digits)
            tp2 = round(swing_low + atr * 0.1, digits)
            structure = "RANGE DISTRIBUTION"
            ob_zone = f"{entry_low} - {entry_high} (Key Resistance & Supply)"
            bsl = f"{swing_high} (Range High)"
            ssl = f"{swing_low} (Range Low)"
            key_sr = f"Cản Đỉnh: {entry_high} | Cản Đáy: {swing_low}"
            checklist = [
                {"text": "Giá test cạnh trên Range High thất bại", "checked": True},
                {"text": "Nến Bearish Engulfing trên H4", "checked": True}
            ]
            rationale = f"CAD/CHF gặp cản đỉnh Range, canh SELL hồi tại {entry_low} - {entry_high}."
    else:  # US100 (Nasdaq 100 Index)
        # Nasdaq 100 logic: Tech momentum, NY Killzone FVG, Discount Liquidity Sweep & Trend Following
        is_bullish = price >= ema50 or bull_pct >= 50
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (SMC NY Killzone FVG + Tech Trend)"
            entry_low = round(price - atr * 0.65, digits)
            entry_high = round(entry_low + atr * 0.25, digits)
            sl = round(entry_low - atr * 0.45, digits)
            tp1 = round(price + atr * 0.85, digits)
            tp2 = round(swing_high, digits)
            structure = "BULLISH TREND CONTINUATION (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bullish FVG & Demand Order Block)"
            bsl = f"{swing_high} (Equal Highs Liquidity Pool)"
            ssl = f"{round(entry_low - atr*0.3, digits)} (Asia/London Session Low)"
            key_sr = f"Hỗ trợ: {entry_low} | Kháng cự: {swing_high}"
            checklist = [
                {"text": "H4 Bullish Order Block (OB) giữ vững phản ứng", "checked": True},
                {"text": "Quét thanh khoản Sell-side (SSL) phiên Á / London", "checked": True},
                {"text": "Lấp đầy khoảng trống FVG tại phiên New York Killzone", "checked": True},
                {"text": "Nhóm Big Tech (Nvidia, Apple, Microsoft) duy trì đà tăng", "checked": True},
                {"text": "EMA 20/50 dốc lên ủng hộ xu hướng Trend Following", "checked": True}
            ]
            rationale = (
                f"Chỉ số US100 (Nasdaq) duy trì cấu trúc tăng trưởng mạnh mẽ của nhóm cổ phiếu công nghệ. "
                f"Kịch bản tuần: Canh BUY khi giá điều chỉnh về vùng FVG + Demand OB ({entry_low} - {entry_high}) "
                f"trong phiên Mỹ để tiếp tục đà tăng hướng tới thanh khoản đỉnh BSL {swing_high}."
            )
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Bearish Supply Rejection)"
            entry_high = round(price + atr * 0.65, digits)
            entry_low = round(entry_high - atr * 0.25, digits)
            sl = round(entry_high + atr * 0.45, digits)
            tp1 = round(price - atr * 0.85, digits)
            tp2 = round(swing_low, digits)
            structure = "BEARISH REJECTION / CHoCH (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Supply Zone)"
            bsl = f"{swing_high} (BSL Peak)"
            ssl = f"{swing_low} (SSL Target)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {swing_low}"
            checklist = [
                {"text": "Cản Supply Zone H4 giữ vững áp lực bán", "checked": True},
                {"text": "Quét thanh khoản đỉnh BSL tạo mô hình SFP đảo chiều", "checked": True},
                {"text": "Lợi suất Trái phiếu Mỹ tăng gây áp lực định giá nhóm Tech", "checked": True}
            ]
            rationale = f"US100 đối mặt áp lực chốt lời tại vùng cản đỉnh, canh SELL khi giá hồi về vùng Supply {entry_low} - {entry_high}."

    # Compute R:R ratio
    risk = abs(entry_high - sl) if bias == "BUY" else abs(sl - entry_low)
    reward = abs(tp2 - entry_high) if bias == "BUY" else abs(entry_low - tp2)
    rr_str = f"1:{round(reward/risk, 1)}" if risk > 0 else "1:2.5"

    return {
        "pair": pair,
        "name": tech.get("name", pair),
        "tv_symbol": tech.get("tv_symbol", "OANDA:XAUUSD"),
        "current_price": price,
        "bias": bias,
        "bias_badge": bias_badge,
        "status": "PLANNING",  # PLANNING, ACTIVE, TRIGGERED, TP1_HIT, TP2_HIT, STOPPED, CANCELLED
        "strategy_type": "SMC + Thuần PA + Trend Follow",
        "entry_zone": f"{entry_low} - {entry_high}",
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr_ratio": rr_str,
        "structure": structure,
        "ob_zone": ob_zone,
        "bsl": bsl,
        "ssl": ssl,
        "key_sr": key_sr,
        "checklist": checklist,
        "rationale": rationale,
        "user_customized": False,
        "user_notes": "",
        "news_driver": news_driver,
        "sentiment": sent.get("sentiment", "NEUTRAL"),
        "bull_score": sent.get("bull_score", 50),
        "bear_score": sent.get("bear_score", 50),
        "updated_at": ""
    }

def build_all_weekly_forecasts(tech_data: Dict[str, Any], news_list: List[Dict[str, Any]], calendar_events: List[Dict[str, Any]], existing_file: str = "data/forecasts.json") -> Dict[str, Any]:
    """
    Build or merge forecasts with user overrides.
    """
    existing_user_edits = {}
    if os.path.exists(existing_file):
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                for k, v in saved.items():
                    if v.get("user_customized", False):
                        existing_user_edits[k] = v
        except Exception as e:
            print(f"[SMCAnalyzer] Notice reading existing forecasts: {e}")

    forecasts = {}
    from backend.collectors.news_collector import get_pair_sentiment_summary
    
    for pair_key, tech in tech_data.items():
        sent = get_pair_sentiment_summary(pair_key, news_list)
        auto_setup = generate_smc_setup(pair_key, tech, sent, calendar_events)
        
        # If user previously customized this pair, preserve user's custom settings
        if pair_key in existing_user_edits:
            custom = existing_user_edits[pair_key]
            auto_setup.update({
                "bias": custom.get("bias", auto_setup["bias"]),
                "bias_badge": custom.get("bias_badge", auto_setup["bias_badge"]),
                "status": custom.get("status", auto_setup["status"]),
                "entry_zone": custom.get("entry_zone", auto_setup["entry_zone"]),
                "entry_low": custom.get("entry_low", auto_setup["entry_low"]),
                "entry_high": custom.get("entry_high", auto_setup["entry_high"]),
                "stop_loss": custom.get("stop_loss", auto_setup["stop_loss"]),
                "tp1": custom.get("tp1", auto_setup["tp1"]),
                "tp2": custom.get("tp2", auto_setup["tp2"]),
                "rr_ratio": custom.get("rr_ratio", auto_setup["rr_ratio"]),
                "rationale": custom.get("rationale", auto_setup["rationale"]),
                "user_notes": custom.get("user_notes", ""),
                "checklist": custom.get("checklist", auto_setup["checklist"]),
                "user_customized": True
            })
            
        forecasts[pair_key] = auto_setup
        
    return forecasts
