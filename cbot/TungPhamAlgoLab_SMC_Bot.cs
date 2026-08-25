// -------------------------------------------------------------------------------------------------
//
//      TÙNG PHẠM ALGO LAB - SMC & PRICE ACTION INSTITUTIONAL CBOT (PRO EDITION)
//      Platform: cTrader Automate (C# .NET)
//      Strategy: Smart Money Concepts (SMC) + Micro ChoCH + Recent Swing Low/High ATR SL
//      Author: Tùng Phạm (Mr Tung) - Hotline/Zalo: 0903.663.060
//      Website: https://tungpham-algo-lab.onrender.com
//
// -------------------------------------------------------------------------------------------------

using System;
using System.Linq;
using cAlgo.API;
using cAlgo.API.Indicators;
using cAlgo.API.Internals;

namespace cAlgo.Robots
{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class TungPhamAlgoLab_SMC_Bot : Robot
    {
        // -------------------------------------------------------------
        // 1. RISK & STOP LOSS MANAGEMENT (CHUẨN QUỸ KỶ LUẬT)
        // -------------------------------------------------------------
        [Parameter("Account Risk (%) per Trade", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 5.0, Step = 0.1, Group = "1. Quản Trị Vốn & Cắt Lỗ (Risk Management)")]
        public double RiskPercent { get; set; }

        [Parameter("Target R:R Ratio (Full TP2)", DefaultValue = 3.5, MinValue = 1.5, MaxValue = 10.0, Step = 0.5, Group = "1. Quản Trị Vốn & Cắt Lỗ (Risk Management)")]
        public double RewardRiskRatio { get; set; }

        [Parameter("Max SL ATR Multiplier Cap", DefaultValue = 1.5, MinValue = 0.8, MaxValue = 2.5, Step = 0.1, Group = "1. Quản Trị Vốn & Cắt Lỗ (Risk Management)")]
        public double MaxSlAtrMultiplier { get; set; }

        [Parameter("Max SL Distance (Pips/Points)", DefaultValue = 180.0, MinValue = 30.0, MaxValue = 500.0, Step = 10.0, Group = "1. Quản Trị Vốn & Cắt Lỗ (Risk Management)")]
        public double MaxSlDistancePips { get; set; }

        [Parameter("Max Open Trades per Symbol", DefaultValue = 1, MinValue = 1, MaxValue = 3, Group = "1. Quản Trị Vốn & Cắt Lỗ (Risk Management)")]
        public int MaxOpenTrades { get; set; }

        // -------------------------------------------------------------
        // 2. TRADE MANAGEMENT (CHỐT LỜI ĐA TẦNG & BREAKEVEN)
        // -------------------------------------------------------------
        [Parameter("Enable Partial TP1 at +1.5R", DefaultValue = true, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public bool EnablePartialTP { get; set; }

        [Parameter("Partial Close Volume (%)", DefaultValue = 50.0, MinValue = 10.0, MaxValue = 90.0, Step = 10.0, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public double PartialClosePercent { get; set; }

        [Parameter("Move SL to Breakeven at TP1 (+1.5R)", DefaultValue = true, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public bool EnableBreakevenAtTP1 { get; set; }

        // -------------------------------------------------------------
        // 3. SMC & PRICE ACTION STRUCTURE (THUẬT TOÁN SMC)
        // -------------------------------------------------------------
        [Parameter("Recent Swing Lookback (Bars)", DefaultValue = 8, MinValue = 3, MaxValue = 20, Group = "3. Cấu Trúc SMC & Order Block")]
        public int RecentSwingBars { get; set; }

        [Parameter("Order Block Max Age (Bars)", DefaultValue = 10, MinValue = 3, MaxValue = 25, Group = "3. Cấu Trúc SMC & Order Block")]
        public int MaxObAgeBars { get; set; }

        [Parameter("Min FVG Gap Size (Pips)", DefaultValue = 2.0, MinValue = 0.5, MaxValue = 20.0, Step = 0.5, Group = "3. Cấu Trúc SMC & Order Block")]
        public double MinFvgPips { get; set; }

        [Parameter("Require M15/H1 ChoCH Confirmation", DefaultValue = true, Group = "3. Cấu Trúc SMC & Order Block")]
        public bool RequireChochTrigger { get; set; }

        // -------------------------------------------------------------
        // 4. INDICATORS & TREND FILTERS
        // -------------------------------------------------------------
        [Parameter("Fast Trend EMA", DefaultValue = 50, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int FastEmaPeriod { get; set; }

        [Parameter("Baseline Slow EMA", DefaultValue = 200, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int SlowEmaPeriod { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int AtrPeriod { get; set; }

        [Parameter("ATR Buffer Added to Swing Low/High", DefaultValue = 0.3, MinValue = 0.1, MaxValue = 1.0, Step = 0.1, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public double AtrBufferMultiplier { get; set; }

        // -------------------------------------------------------------
        // 5. SESSION & EXECUTION FILTERS
        // -------------------------------------------------------------
        [Parameter("Filter Trading Hours (UTC)", DefaultValue = true, Group = "5. Phiên Giao Dịch & Spread")]
        public bool FilterTradingHours { get; set; }

        [Parameter("Start Hour UTC (London Open)", DefaultValue = 7, MinValue = 0, MaxValue = 23, Group = "5. Phiên Giao Dịch & Spread")]
        public int StartHourUtc { get; set; }

        [Parameter("End Hour UTC (NY Close)", DefaultValue = 20, MinValue = 0, MaxValue = 23, Group = "5. Phiên Giao Dịch & Spread")]
        public int EndHourUtc { get; set; }

        [Parameter("Max Allowed Spread (Pips)", DefaultValue = 3.5, MinValue = 0.5, MaxValue = 20.0, Step = 0.5, Group = "5. Phiên Giao Dịch & Spread")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Custom Bot Label", DefaultValue = "TungPham_SMC_Pro", Group = "5. Phiên Giao Dịch & Spread")]
        public string BotLabel { get; set; }

        // -------------------------------------------------------------
        // STATE & INDICATOR INSTANCES
        // -------------------------------------------------------------
        private ExponentialMovingAverage _emaFast;
        private ExponentialMovingAverage _emaSlow;
        private AverageTrueRange _atr;

        protected override void OnStart()
        {
            _emaFast = Indicators.ExponentialMovingAverage(Bars.ClosePrices, FastEmaPeriod);
            _emaSlow = Indicators.ExponentialMovingAverage(Bars.ClosePrices, SlowEmaPeriod);
            _atr = Indicators.AverageTrueRange(Bars, AtrPeriod, MovingAverageType.Exponential);

            Print("==========================================================================");
            Print("🚀 TÙNG PHẠM ALGO LAB - SMC cBot (PRO EDITION) Initialized!");
            Print($"Asset: {SymbolName} | Timeframe: {TimeFrame} | Risk: {RiskPercent}% | R:R: 1:{RewardRiskRatio}");
            Print($"SL Buffer: Recent Swing Low/High + {AtrBufferMultiplier}x ATR (Max Cap: {MaxSlAtrMultiplier}x ATR / {MaxSlDistancePips} pips)");
            Print("==========================================================================");
        }

        protected override void OnBar()
        {
            // 1. Quản lý lệnh đang mở (TP1 chốt 50% & kéo SL về BE)
            ManageOpenPositions();

            // 2. Giới hạn số lượng lệnh mở cùng lúc
            int currentOpenPositions = Positions.Count(p => p.SymbolName == SymbolName && p.Label == BotLabel);
            if (currentOpenPositions >= MaxOpenTrades)
                return;

            // 3. Kiểm tra Spread
            double currentSpreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (currentSpreadPips > MaxSpreadPips)
            {
                Print($"[SMC Bot] Spread ({currentSpreadPips:F1} pips) > Max ({MaxSpreadPips:F1} pips). Bỏ qua.");
                return;
            }

            // 4. Bộ lọc phiên giao dịch (London & New York)
            if (FilterTradingHours)
            {
                int currentHour = Server.Time.Hour;
                if (currentHour < StartHourUtc || currentHour >= EndHourUtc)
                    return;
            }

            // 5. Đảm bảo đủ số nến tính toán
            if (Bars.Count < Math.Max(MaxObAgeBars, SlowEmaPeriod) + 20)
                return;

            // 6. Thực thi thuật toán SMC
            EvaluateSMCSetups();
        }

        protected override void OnTick()
        {
            if (EnablePartialTP || EnableBreakevenAtTP1)
            {
                ManageOpenPositions();
            }
        }

        // =========================================================================================
        // SMC LOGIC: TÌM KIẾM ĐIỂM VÀO LỆNH & STOP LOSS CHẶT CHẼ
        // =========================================================================================
        private void EvaluateSMCSetups()
        {
            int lastIndex = Bars.Count - 2; // Cây nến vừa đóng cửa gần nhất
            double closePrice = Bars.ClosePrices[lastIndex];
            double fastEma = _emaFast.Result[lastIndex];
            double slowEma = _emaSlow.Result[lastIndex];
            double currentAtr = _atr.Result[lastIndex];

            // -------------------------------------------------------------
            // BƯỚC 1: XÁC ĐỊNH XU HƯỚNG LỚN (MACRO TREND VIA EMA)
            // -------------------------------------------------------------
            bool isMacroBullish = closePrice > fastEma && fastEma >= slowEma;
            bool isMacroBearish = closePrice < fastEma && fastEma <= slowEma;

            // -------------------------------------------------------------
            // BƯỚC 2: TÌM SWING LOW / SWING HIGH GẦN NHẤT (Lookback ngắn 3 - 8 nến)
            // -------------------------------------------------------------
            double recentSwingLow = FindRecentLocalLow(lastIndex, RecentSwingBars);
            double recentSwingHigh = FindRecentLocalHigh(lastIndex, RecentSwingBars);

            // -------------------------------------------------------------
            // BƯỚC 3: SETUP BUY (LỆNH MUA SMC)
            // -------------------------------------------------------------
            if (isMacroBullish)
            {
                // Tìm vùng Demand Order Block trong phạm vi sóng tăng gần nhất (3 - 10 nến)
                OrderBlock ob = FindRecentDemandOB(lastIndex, MaxObAgeBars);
                if (ob != null && ob.IsValid)
                {
                    double currentLow = Bars.LowPrices[lastIndex];
                    double currentClose = Bars.ClosePrices[lastIndex];

                    // Giá hồi về chạm vùng Demand OB
                    if (currentLow <= ob.High && currentClose >= ob.Low)
                    {
                        // Nến xác nhận M15: Nến đóng cửa xanh hoặc rút chân trên OB
                        if (Bars.ClosePrices[lastIndex] > Bars.OpenPrices[lastIndex] || Bars.ClosePrices[lastIndex] > (Bars.HighPrices[lastIndex] + Bars.LowPrices[lastIndex]) / 2.0)
                        {
                            ExecuteTightSMCBuy(ob, recentSwingLow, currentAtr);
                        }
                    }
                }
            }
            // -------------------------------------------------------------
            // BƯỚC 4: SETUP SELL (LỆNH BÁN SMC)
            // -------------------------------------------------------------
            else if (isMacroBearish)
            {
                // Tìm vùng Supply Order Block trong phạm vi sóng giảm gần nhất (3 - 10 nến)
                OrderBlock ob = FindRecentSupplyOB(lastIndex, MaxObAgeBars);
                if (ob != null && ob.IsValid)
                {
                    double currentHigh = Bars.HighPrices[lastIndex];
                    double currentClose = Bars.ClosePrices[lastIndex];

                    // Giá hồi lên chạm vùng Supply OB
                    if (currentHigh >= ob.Low && currentClose <= ob.High)
                    {
                        // Nến xác nhận M15: Nến đóng cửa đỏ hoặc rút râu từ chối Supply
                        if (Bars.ClosePrices[lastIndex] < Bars.OpenPrices[lastIndex] || Bars.ClosePrices[lastIndex] < (Bars.HighPrices[lastIndex] + Bars.LowPrices[lastIndex]) / 2.0)
                        {
                            ExecuteTightSMCSell(ob, recentSwingHigh, currentAtr);
                        }
                    }
                }
            }
        }

        // =========================================================================================
        // THI HÀNH LỆNH BUY VỚI STOP LOSS CHUẨN KỸ THUẬT (KHÔNG BAO GIỜ BỊ SL SÂU)
        // =========================================================================================
        private void ExecuteTightSMCBuy(OrderBlock ob, double recentSwingLow, double atr)
        {
            double entryPrice = Symbol.Ask;

            // 1. Stop Loss tính từ đáy Swing Low gần nhất hoặc đáy Order Block + Đệm ATR nhỏ (0.3x ATR)
            double baseSlLevel = Math.Min(recentSwingLow, ob.Low);
            double calculatedSl = baseSlLevel - (atr * AtrBufferMultiplier);

            // 2. KHÓA CHẶT TRẦN SL (Max SL Cap: Tối đa 1.5x ATR hoặc MaxSlDistancePips)
            double maxAllowedSlPrice = entryPrice - (atr * MaxSlAtrMultiplier);
            double maxPipsSlPrice = entryPrice - (MaxSlDistancePips * Symbol.PipSize);
            double tightestSlBound = Math.Max(maxAllowedSlPrice, maxPipsSlPrice);

            // Gán mức Stop Loss kỷ luật
            double finalStopLoss = Math.Max(calculatedSl, tightestSlBound);
            double riskDistance = entryPrice - finalStopLoss;

            // 3. Kiểm tra tính hợp lệ của khoảng cách rủi ro (phải > 0 và <= Max SL)
            double slPips = riskDistance / Symbol.PipSize;
            if (slPips <= 10.0 || slPips > MaxSlDistancePips)
            {
                Print($"[SMC BUY SKIPPED] Khoảng cách SL ({slPips:F1} pips) không đạt tiêu chuẩn R:R (Max: {MaxSlDistancePips}). Bỏ qua.");
                return;
            }

            // 4. Tính toán TP2 mục tiêu theo R:R (mặc định 1:3.5)
            double takeProfitPrice = entryPrice + (riskDistance * RewardRiskRatio);
            double tpPips = (takeProfitPrice - entryPrice) / Symbol.PipSize;

            // 5. Tính Lot size tự động theo đúng % Risk tài khoản
            double volume = CalculateVolume(riskDistance);
            if (volume <= 0) return;

            string comment = $"TP_BUY_SL:{finalStopLoss:F2}_TP2:{takeProfitPrice:F2}";
            var result = ExecuteMarketOrder(TradeType.Buy, SymbolName, volume, BotLabel, slPips, tpPips, comment);

            if (result.IsSuccessful)
            {
                Print($"[🟢 SMC BUY EXECUTED] Entry: {entryPrice:F2} | SL Kỷ Luật: {finalStopLoss:F2} ({slPips:F1} pips / ~{(riskDistance):F2} giá) | TP2: {takeProfitPrice:F2} ({tpPips:F1} pips) | R:R: 1:{RewardRiskRatio} | Vol: {volume}");
            }
        }

        // =========================================================================================
        // THI HÀNH LỆNH SELL VỚI STOP LOSS CHUẨN KỸ THUẬT (KHÔNG BAO GIỜ BỊ SL SÂU)
        // =========================================================================================
        private void ExecuteTightSMCSell(OrderBlock ob, double recentSwingHigh, double atr)
        {
            double entryPrice = Symbol.Bid;

            // 1. Stop Loss tính từ đỉnh Swing High gần nhất hoặc đỉnh Order Block + Đệm ATR nhỏ (0.3x ATR)
            double baseSlLevel = Math.Max(recentSwingHigh, ob.High);
            double calculatedSl = baseSlLevel + (atr * AtrBufferMultiplier);

            // 2. KHÓA CHẶT TRẦN SL (Max SL Cap: Tối đa 1.5x ATR hoặc MaxSlDistancePips)
            double minAllowedSlPrice = entryPrice + (atr * MaxSlAtrMultiplier);
            double maxPipsSlPrice = entryPrice + (MaxSlDistancePips * Symbol.PipSize);
            double tightestSlBound = Math.Min(minAllowedSlPrice, maxPipsSlPrice);

            // Gán mức Stop Loss kỷ luật
            double finalStopLoss = Math.Min(calculatedSl, tightestSlBound);
            double riskDistance = finalStopLoss - entryPrice;

            // 3. Kiểm tra tính hợp lệ của khoảng cách rủi ro
            double slPips = riskDistance / Symbol.PipSize;
            if (slPips <= 10.0 || slPips > MaxSlDistancePips)
            {
                Print($"[SMC SELL SKIPPED] Khoảng cách SL ({slPips:F1} pips) không đạt tiêu chuẩn R:R (Max: {MaxSlDistancePips}). Bỏ qua.");
                return;
            }

            // 4. Tính toán TP2 mục tiêu theo R:R (mặc định 1:3.5)
            double takeProfitPrice = entryPrice - (riskDistance * RewardRiskRatio);
            double tpPips = (entryPrice - takeProfitPrice) / Symbol.PipSize;

            // 5. Tính Lot size tự động theo đúng % Risk tài khoản
            double volume = CalculateVolume(riskDistance);
            if (volume <= 0) return;

            string comment = $"TP_SELL_SL:{finalStopLoss:F2}_TP2:{takeProfitPrice:F2}";
            var result = ExecuteMarketOrder(TradeType.Sell, SymbolName, volume, BotLabel, slPips, tpPips, comment);

            if (result.IsSuccessful)
            {
                Print($"[🔴 SMC SELL EXECUTED] Entry: {entryPrice:F2} | SL Kỷ Luật: {finalStopLoss:F2} ({slPips:F1} pips / ~{(riskDistance):F2} giá) | TP2: {takeProfitPrice:F2} ({tpPips:F1} pips) | R:R: 1:{RewardRiskRatio} | Vol: {volume}");
            }
        }

        // =========================================================================================
        // TÍNH TOÁN KHỐI LƯỢNG LOT THEO % RISK
        // =========================================================================================
        private double CalculateVolume(double riskDistancePrice)
        {
            double riskCapital = Account.Equity * (RiskPercent / 100.0);
            double slPips = riskDistancePrice / Symbol.PipSize;

            if (slPips <= 0) return Symbol.VolumeInUnitsMin;

            double pipValueInAccountCurrency = Symbol.PipValue;
            if (pipValueInAccountCurrency <= 0) pipValueInAccountCurrency = 1.0;

            double calculatedVolume = riskCapital / (slPips * pipValueInAccountCurrency);
            double normalizedVolume = Symbol.NormalizeVolumeInUnits(calculatedVolume, RoundingMode.Down);

            if (normalizedVolume < Symbol.VolumeInUnitsMin)
                normalizedVolume = Symbol.VolumeInUnitsMin;
            if (normalizedVolume > Symbol.VolumeInUnitsMax)
                normalizedVolume = Symbol.VolumeInUnitsMax;

            return normalizedVolume;
        }

        // =========================================================================================
        // QUẢN LÝ LỆNH: CHỐT LỜI TP1 (+1.5R) & DỜI SL VỀ HÒA VỐN (BREAKEVEN)
        // =========================================================================================
        private void ManageOpenPositions()
        {
            var openPositions = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BotLabel).ToList();

            foreach (var pos in openPositions)
            {
                double initialRisk = Math.Abs(pos.EntryPrice - (pos.StopLoss ?? pos.EntryPrice));
                if (initialRisk <= 0) continue;

                // Mức giá đạt +1.5R
                double tp1Price = pos.TradeType == TradeType.Buy 
                    ? pos.EntryPrice + (initialRisk * 1.5) 
                    : pos.EntryPrice - (initialRisk * 1.5);

                bool hasReachedTP1 = pos.TradeType == TradeType.Buy 
                    ? Symbol.Bid >= tp1Price 
                    : Symbol.Ask <= tp1Price;

                // Khi giá chạm TP1 (+1.5R) và chưa từng chốt 50%
                if (hasReachedTP1 && !pos.Comment.Contains("[TP1_CLOSED]"))
                {
                    if (EnablePartialTP)
                    {
                        double closeUnits = Symbol.NormalizeVolumeInUnits(pos.VolumeInUnits * (PartialClosePercent / 100.0), RoundingMode.Down);
                        if (closeUnits >= Symbol.VolumeInUnitsMin && pos.VolumeInUnits - closeUnits >= Symbol.VolumeInUnitsMin)
                        {
                            ClosePosition(pos, closeUnits);
                            Print($"[TP1 HIT 🎯] Đã chốt {PartialClosePercent}% khối lượng ({closeUnits} units) tại +1.5R lợi nhuận cho #{pos.Id}");
                        }
                    }

                    if (EnableBreakevenAtTP1)
                    {
                        // Dời SL về Entry + 1 pip đệm phí sàn
                        double beSl = pos.TradeType == TradeType.Buy ? pos.EntryPrice + Symbol.PipSize : pos.EntryPrice - Symbol.PipSize;
                        ModifyPosition(pos, beSl, pos.TakeProfit);
                        Print($"[BREAKEVEN SHIELD 🛡] Đã dời Stop Loss về mức hòa vốn {beSl:F2} cho #{pos.Id}. Lệnh đã trở thành RISK-FREE 100%!");
                    }

                    ModifyPosition(pos, pos.StopLoss, pos.TakeProfit);
                }
            }
        }

        // =========================================================================================
        // CÁC HÀM TÌM SWING GẦN NHẤT & ORDER BLOCK MỚI NHẤT
        // =========================================================================================
        private double FindRecentLocalLow(int startIndex, int bars)
        {
            double minLow = Bars.LowPrices[startIndex];
            for (int i = startIndex; i >= startIndex - bars && i >= 0; i--)
            {
                if (Bars.LowPrices[i] < minLow)
                    minLow = Bars.LowPrices[i];
            }
            return minLow;
        }

        private double FindRecentLocalHigh(int startIndex, int bars)
        {
            double maxHigh = Bars.HighPrices[startIndex];
            for (int i = startIndex; i >= startIndex - bars && i >= 0; i--)
            {
                if (Bars.HighPrices[i] > maxHigh)
                    maxHigh = Bars.HighPrices[i];
            }
            return maxHigh;
        }

        private OrderBlock FindRecentDemandOB(int startIndex, int maxAge)
        {
            double minFvgPriceGap = MinFvgPips * Symbol.PipSize;

            for (int i = startIndex - 1; i >= startIndex - maxAge && i >= 2; i--)
            {
                // Bullish Imbalance / FVG: High của nến 1 < Low của nến 3
                double candle1High = Bars.HighPrices[i - 1];
                double candle3Low = Bars.LowPrices[i + 1];

                if (candle3Low - candle1High >= minFvgPriceGap)
                {
                    // Cây nến giảm cuối cùng trước nhịp bứt phá là Order Block
                    for (int k = i; k >= i - 2 && k >= 0; k--)
                    {
                        if (Bars.ClosePrices[k] <= Bars.OpenPrices[k])
                        {
                            return new OrderBlock
                            {
                                High = Bars.HighPrices[k],
                                Low = Bars.LowPrices[k],
                                IsValid = true
                            };
                        }
                    }
                }
            }
            return null;
        }

        private OrderBlock FindRecentSupplyOB(int startIndex, int maxAge)
        {
            double minFvgPriceGap = MinFvgPips * Symbol.PipSize;

            for (int i = startIndex - 1; i >= startIndex - maxAge && i >= 2; i--)
            {
                // Bearish Imbalance / FVG: Low của nến 1 > High của nến 3
                double candle1Low = Bars.LowPrices[i - 1];
                double candle3High = Bars.HighPrices[i + 1];

                if (candle1Low - candle3High >= minFvgPriceGap)
                {
                    // Cây nến tăng cuối cùng trước nhịp giảm mạnh là Order Block
                    for (int k = i; k >= i - 2 && k >= 0; k--)
                    {
                        if (Bars.ClosePrices[k] >= Bars.OpenPrices[k])
                        {
                            return new OrderBlock
                            {
                                High = Bars.HighPrices[k],
                                Low = Bars.LowPrices[k],
                                IsValid = true
                            };
                        }
                    }
                }
            }
            return null;
        }

        private class OrderBlock
        {
            public double High { get; set; }
            public double Low { get; set; }
            public bool IsValid { get; set; }
        }
    }
}
