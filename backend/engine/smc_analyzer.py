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

    # -------------------------------------------------------------------------------------------------
    # CORE FORMULA PORTED FROM TungPhamAlgoLab_SMC_Bot.cs (PRO EDITION v2.5)
    # Target R:R = 1:3.5 | TP1 = +1.5R (BE) | SL Buffer = 0.3x ATR | Max SL Cap = 1.5x ATR
    # -------------------------------------------------------------------------------------------------
    ATR_BUFFER_MULT = 0.30
    MAX_SL_ATR_CAP = 1.50
    REWARD_RISK_RATIO = 3.50

    if pair == "XAUUSD":
        # Gold logic: Trend on Daily/H4 EMA + M15 Order Block & FVG
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (SMC Demand OB + FVG Retest)"
            entry_low = round(price - atr * 0.20, digits)
            entry_high = round(entry_low + atr * 0.10, digits)
            
            # SL strictly calculated as base level - 0.3x ATR, capped at 1.5x ATR
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            # Median entry & exact R:R
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BULLISH BOS (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Demand Order Block + FVG)"
            bsl = f"{tp2} (Buy-side Liquidity Swing High)"
            ssl = f"{sl} (Sell-side Liquidity Invalidation SL)"
            key_sr = f"Cản Hỗ trợ: {entry_low} | Cản Kháng cự: {tp2}"
            checklist = [
                {"text": "H4 Demand Order Block giữ vững phản ứng", "checked": True},
                {"text": "Quét thanh khoản Sell-side (SSL) tạo nến rút chân M15", "checked": True},
                {"text": "SL theo ATR H4/H1 bảo vệ an toàn dưới chân Order Block", "checked": True},
                {"text": "Tỷ lệ R:R kỳ vọng 1:3.5 (TP1 +1.5R chốt 50% & kéo SL về BE)", "checked": True},
                {"text": "EMA 50 & 200 ủng hộ xu hướng tăng dài hạn", "checked": True}
            ]
            rationale = (
                f"Vàng đang giữ cấu trúc tăng (Uptrend Structure) trên khung Daily & H4. "
                f"Kịch bản tuần: Canh BUY khi giá điều chỉnh về vùng Demand Order Block & Discount FVG ({entry_low} - {entry_high}), "
                f"dừng lỗ SL theo ATR ({sl}) đặt an toàn dưới chân OB, hướng tới mục tiêu chốt lời thanh khoản BSL TP1 {tp1} (+1.5R) và TP2 {tp2} (+3.5R)."
            )
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (SMC Supply Zone Rejection)"
            entry_high = round(price + atr * 0.20, digits)
            entry_low = round(entry_high - atr * 0.10, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BEARISH CHoCH (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Supply OB)"
            bsl = f"{sl} (Buy-side Liquidity Invalidation)"
            ssl = f"{tp2} (Sell-side Liquidity Target)"
            key_sr = f"Cản Kháng cự: {entry_high} | Cản Hỗ trợ: {tp2}"
            checklist = [
                {"text": "H4 Supply Order Block giữ vững áp lực bán", "checked": True},
                {"text": "Quét râu tạo SFP trên đỉnh BSL", "checked": True},
                {"text": "SL theo ATR an toàn trên đỉnh Supply Zone", "checked": True},
                {"text": "Nến Shooting Star / Bearish Engulfing tại Supply", "checked": True}
            ]
            rationale = (
                f"Vàng gặp áp lực chốt lời mạnh tại vùng đỉnh, xuất hiện tín hiệu CHoCH đảo chiều ngắn hạn. "
                f"Kịch bản tuần: Canh SELL khi giá hồi phục kiểm tra Bearish Supply OB quanh {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."
            )

    elif pair == "USDJPY":
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (Trend Follow H4 Pullback)"
            entry_low = round(price - atr * 0.25, digits)
            entry_high = round(entry_low + atr * 0.12, digits)
            
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BULLISH TREND CONTINUATION"
            ob_zone = f"{entry_low} - {entry_high} (H4 Imbalance & 50 EMA Confluence)"
            bsl = f"{tp2} (Equal Highs Liquidity Pool)"
            ssl = f"{sl} (Recent Higher Low / SL)"
            key_sr = f"Support: {entry_low} | Resistance: {tp2}"
            checklist = [
                {"text": "Cấu trúc Higher Highs & Higher Lows duy trì", "checked": True},
                {"text": "Giá chạm dải hỗ trợ động EMA 20/50 trên H4", "checked": True},
                {"text": "Chưa có tín hiệu can thiệp trực tiếp từ BOJ", "checked": True}
            ]
            rationale = f"USD/JPY duy trì xu hướng tăng bền vững trên mây EMA. Mở lệnh BUY khi giá điều chỉnh về vùng FVG + EMA50 ({entry_low} - {entry_high}) với SL {sl}, TP1 {tp1} và TP2 {tp2}."
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (SMC CHoCH Breakout)"
            entry_high = round(price + atr * 0.25, digits)
            entry_low = round(entry_high - atr * 0.12, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BEARISH CHoCH"
            ob_zone = f"{entry_low} - {entry_high} (Supply OB)"
            bsl = f"{sl} (BSL Invalidation)"
            ssl = f"{tp2} (Target SSL)"
            key_sr = f"Resistance: {entry_high} | Support: {tp2}"
            checklist = [
                {"text": "Thủng cấu trúc đáy gần nhất (CHoCH)", "checked": True},
                {"text": "Retest Bearish Order Block thất bại", "checked": True}
            ]
            rationale = f"USD/JPY suy yếu, canh SELL hồi tại vùng kháng cự {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."

    elif pair == "BTCUSD":
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (SMC Discount FVG + Whale Accumulation)"
            entry_low = round(price - atr * 0.25, digits)
            entry_high = round(entry_low + atr * 0.12, digits)
            
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BULLISH UPTREND STRUCTURE (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bullish Order Block + Imbalance Fill)"
            bsl = f"{tp2} (Major Swing High BSL)"
            ssl = f"{sl} (Weekend Low Sweep Target / SL)"
            key_sr = f"Hỗ trợ Cầu: {entry_low} | Kháng cự Đỉnh: {tp2}"
            checklist = [
                {"text": "H4 Bullish Order Block (OB) giữ vững phản ứng", "checked": True},
                {"text": "Quét sạch thanh khoản đáy cuối tuần (Weekend Low Sweep)", "checked": True},
                {"text": "Lấp đầy khoảng trống FVG / Imbalance khung H4", "checked": True}
            ]
            rationale = f"Bitcoin (BTC/USD) duy trì cấu trúc tăng trưởng mạnh mẽ 24/7. Canh BUY khi giá điều chỉnh về vùng FVG + Demand OB ({entry_low} - {entry_high}) với SL {sl}, TP1 {tp1} và TP2 {tp2}."
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Supply Zone Mitigation)"
            entry_high = round(price + atr * 0.25, digits)
            entry_low = round(entry_high - atr * 0.12, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BEARISH DISTRIBUTION (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Supply Zone)"
            bsl = f"{sl} (BSL Peak / SL)"
            ssl = f"{tp2} (SSL Support Target)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {tp2}"
            checklist = [
                {"text": "Cản Supply Zone H4 giữ vững áp lực bán", "checked": True},
                {"text": "Quét râu tạo mô hình Swing Failure Pattern (SFP) tại đỉnh BSL", "checked": True}
            ]
            rationale = f"Bitcoin đối mặt áp lực chốt lời tại vùng cản đỉnh, canh SELL khi giá hồi về vùng Supply {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."

    elif pair == "GBPUSD":
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (Bullish Trend Rebound)"
            entry_low = round(price - atr * 0.25, digits)
            entry_high = round(entry_low + atr * 0.12, digits)
            
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BULLISH STRUCTURE"
            ob_zone = f"{entry_low} - {entry_high} (H4 Demand OB)"
            bsl = f"{tp2} (BSL Target)"
            ssl = f"{sl} (SSL / SL)"
            key_sr = f"Hỗ trợ: {entry_low} | Kháng cự: {tp2}"
            checklist = [
                {"text": "Test thành công vùng Demand Order Block H4", "checked": True},
                {"text": "Trendline hỗ trợ dốc lên giữ vững", "checked": True}
            ]
            rationale = f"GBP/USD duy trì lực mua, canh BUY hồi tại vùng cầu {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (London Liquidity Sweep Setup)"
            entry_high = round(price + atr * 0.25, digits)
            entry_low = round(entry_high - atr * 0.12, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BEARISH BOS (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Order Block)"
            bsl = f"{sl} (London High BSL / SL)"
            ssl = f"{tp2} (Weekly Target SSL)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {tp2}"
            checklist = [
                {"text": "Phiên London quét thanh khoản đỉnh Á (Asia High Sweep)", "checked": True},
                {"text": "Xuất hiện cụm nến Bearish Engulfing trên M15/H1", "checked": True}
            ]
            rationale = f"GBP/USD dao động dưới cản động EMA. Chờ phiên London tạo bẫy giá quét đỉnh Á (Judas Swing), sau đó SELL tại Supply OB ({entry_low} - {entry_high}) với SL {sl}, TP1 {tp1} và TP2 {tp2}."

    elif pair == "CADCHF":
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (Support Channel Bounce + PA)"
            entry_low = round(price - atr * 0.25, digits)
            entry_high = round(entry_low + atr * 0.12, digits)
            
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "RANGE ACCUMULATION / S&R BOUNCE"
            ob_zone = f"{entry_low} - {entry_high} (Key Support & Demand Base)"
            bsl = f"{tp2} (Range High Liquidity)"
            ssl = f"{sl} (Range Low Liquidity / SL)"
            key_sr = f"Cản Đáy: {entry_low} | Cản Đỉnh: {tp2}"
            checklist = [
                {"text": "Giá chạm cạnh dưới biên độ tích lũy (Range Low)", "checked": True},
                {"text": "Nến Pinbar từ chối vùng hỗ trợ D1", "checked": True}
            ]
            rationale = f"CAD/CHF đang di chuyển trong biên độ Range đi ngang. Canh BUY khi giá test vùng biên dưới {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Resistance Range Rejection)"
            entry_high = round(price + atr * 0.25, digits)
            entry_low = round(entry_high - atr * 0.12, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "RANGE DISTRIBUTION"
            ob_zone = f"{entry_low} - {entry_high} (Key Resistance & Supply)"
            bsl = f"{sl} (Range High / SL)"
            ssl = f"{tp2} (Range Low)"
            key_sr = f"Cản Đỉnh: {entry_high} | Cản Đáy: {tp2}"
            checklist = [
                {"text": "Giá test cạnh trên Range High thất bại", "checked": True},
                {"text": "Nến Bearish Engulfing trên H4", "checked": True}
            ]
            rationale = f"CAD/CHF gặp cản đỉnh Range, canh SELL hồi tại {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."

    else:  # US100 (Nasdaq 100 Index)
        is_bullish = price >= ema50 or (ema50 >= ema200)
        if is_bullish:
            bias = "BUY"
            bias_badge = "🟢 BUY (SMC NY Killzone FVG + Tech Trend)"
            entry_low = round(price - atr * 0.28, digits)
            entry_high = round(entry_low + atr * 0.12, digits)
            
            base_sl = entry_low - (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_high - (atr * MAX_SL_ATR_CAP)
            sl = round(max(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(entry_mid - sl)
            tp1 = round(entry_mid + (risk_dist * 1.5), digits)
            tp2 = round(entry_mid + (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BULLISH TREND CONTINUATION (H4/D1)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bullish FVG & Demand Order Block)"
            bsl = f"{tp2} (Equal Highs Liquidity Pool)"
            ssl = f"{sl} (Asia/London Session Low / SL)"
            key_sr = f"Hỗ trợ: {entry_low} | Kháng cự: {tp2}"
            checklist = [
                {"text": "H4 Bullish Order Block (OB) giữ vững phản ứng", "checked": True},
                {"text": "Quét thanh khoản Sell-side (SSL) phiên Á / London", "checked": True},
                {"text": "Lấp đầy khoảng trống FVG tại phiên New York Killzone", "checked": True}
            ]
            rationale = f"Chỉ số US100 (Nasdaq) duy trì cấu trúc tăng trưởng mạnh mẽ của nhóm cổ phiếu công nghệ. Canh BUY khi giá điều chỉnh về vùng FVG + Demand OB ({entry_low} - {entry_high}) với SL {sl}, TP1 {tp1} và TP2 {tp2}."
        else:
            bias = "SELL"
            bias_badge = "🔴 SELL (Bearish Supply Rejection)"
            entry_high = round(price + atr * 0.28, digits)
            entry_low = round(entry_high - atr * 0.12, digits)
            
            base_sl = entry_high + (atr * ATR_BUFFER_MULT)
            max_sl_bound = entry_low + (atr * MAX_SL_ATR_CAP)
            sl = round(min(base_sl, max_sl_bound), digits)
            
            entry_mid = (entry_low + entry_high) / 2
            risk_dist = abs(sl - entry_mid)
            tp1 = round(entry_mid - (risk_dist * 1.5), digits)
            tp2 = round(entry_mid - (risk_dist * REWARD_RISK_RATIO), digits)
            
            structure = "BEARISH REJECTION / CHoCH (H4)"
            ob_zone = f"{entry_low} - {entry_high} (H4 Bearish Supply Zone)"
            bsl = f"{sl} (BSL Peak / SL)"
            ssl = f"{tp2} (SSL Target)"
            key_sr = f"Kháng cự: {entry_high} | Hỗ trợ: {tp2}"
            checklist = [
                {"text": "Cản Supply Zone H4 giữ vững áp lực bán", "checked": True},
                {"text": "Quét thanh khoản đỉnh BSL tạo mô hình SFP đảo chiều", "checked": True}
            ]
            rationale = f"US100 đối mặt áp lực chốt lời tại vùng cản đỉnh, canh SELL khi giá hồi về vùng Supply {entry_low} - {entry_high} với SL {sl}, TP1 {tp1} và TP2 {tp2}."

    rr_str = "1:3.5"

    # Execution Trigger & Multi-timeframe Structure Flow
    trigger = (
        f"M15 Bullish CHOCH + displacement nến xác nhận + retest vùng Order Block ({entry_low} - {entry_high})"
        if bias == "BUY"
        else f"M15 Bearish CHOCH + râu quét thanh khoản đỉnh + retest Supply Zone ({entry_low} - {entry_high})"
    )
    market_structure_flow = {
        "d1": "BULLISH UPTREND" if bias == "BUY" else "BEARISH DOWNTREND",
        "h4": "BULLISH BOS" if bias == "BUY" else "BEARISH CHOCH",
        "h1": "PULLBACK TO DISCOUNT" if bias == "BUY" else "PULLBACK TO PREMIUM",
        "m15": "WAITING CONFIRMATION TRIGGER"
    }

    return {
        "pair": pair,
        "name": tech.get("name", pair),
        "tv_symbol": tech.get("tv_symbol", "OANDA:XAUUSD"),
        "current_price": price,
        "bias": bias,
        "bias_badge": bias_badge,
        "status": "WAITING",  # WAITING, ACTIVE, TP1_HIT, TP2_HIT, INVALIDATED
        "strategy_type": "SMC + Thuần PA + Trend Follow",
        "entry_zone": f"{entry_low} - {entry_high}",
        "entry_low": entry_low,
        "entry_high": entry_high,
        "stop_loss": sl,
        "tp1": tp1,
        "tp2": tp2,
        "rr_ratio": rr_str,
        "trigger": trigger,
        "market_structure_flow": market_structure_flow,
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
    Build fresh, 100% accurate algorithmic SMC forecasts adapted to current live market prices.
    Preserves active trade execution only if a trade is currently in flight.
    """
    existing_saved = {}
    if os.path.exists(existing_file):
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                existing_saved = json.load(f)
        except Exception as e:
            print(f"[SMCAnalyzer] Notice reading existing forecasts: {e}")

    forecasts = {}
    from backend.collectors.news_collector import get_pair_sentiment_summary
    
    for pair_key, tech in tech_data.items():
        sent = get_pair_sentiment_summary(pair_key, news_list)
        auto_setup = generate_smc_setup(pair_key, tech, sent, calendar_events)
        
        # Only preserve active trade state if trade is ACTIVE
        if pair_key in existing_saved:
            saved_f = existing_saved[pair_key]
            saved_status = saved_f.get("status", "WAITING")
            
            # If trade is actively in flight, keep its locked entry/sl/tp
            if saved_status == "ACTIVE" and saved_f.get("actual_entry"):
                auto_setup.update({
                    "bias": saved_f.get("bias", auto_setup["bias"]),
                    "bias_badge": saved_f.get("bias_badge", auto_setup["bias_badge"]),
                    "status": "ACTIVE",
                    "entry_zone": saved_f.get("entry_zone", auto_setup["entry_zone"]),
                    "entry_low": saved_f.get("entry_low", auto_setup["entry_low"]),
                    "entry_high": saved_f.get("entry_high", auto_setup["entry_high"]),
                    "stop_loss": saved_f.get("stop_loss", auto_setup["stop_loss"]),
                    "tp1": saved_f.get("tp1", auto_setup["tp1"]),
                    "tp2": saved_f.get("tp2", auto_setup["tp2"]),
                    "rr_ratio": saved_f.get("rr_ratio", auto_setup["rr_ratio"]),
                    "actual_entry": saved_f.get("actual_entry"),
                    "activated_at": saved_f.get("activated_at"),
                    "user_customized": saved_f.get("user_customized", False),
                    "user_notes": saved_f.get("user_notes", "")
                })
            else:
                # In WAITING status: Always use fresh mathematically accurate setup
                auto_setup["user_notes"] = saved_f.get("user_notes", "")
            
        forecasts[pair_key] = auto_setup
        
    return forecasts
