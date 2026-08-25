// -------------------------------------------------------------------------------------------------
//
//      TÙNG PHẠM ALGO LAB - SMC & PRICE ACTION INSTITUTIONAL CBOT
//      Platform: cTrader Automate (C# .NET)
//      Strategy: Smart Money Concepts (SMC) + Order Block + FVG + Liquidity Sweep + Dynamic ATR SL
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
        // PARAMETERS: Risk Management & Account Sizing
        // -------------------------------------------------------------
        [Parameter("Account Risk (%) per Trade", DefaultValue = 1.0, MinValue = 0.1, MaxValue = 10.0, Step = 0.1, Group = "1. Quản Trị Vốn (Risk Management)")]
        public double RiskPercent { get; set; }

        [Parameter("Reward-to-Risk Ratio (Full TP2)", DefaultValue = 3.5, MinValue = 1.5, MaxValue = 10.0, Step = 0.5, Group = "1. Quản Trị Vốn (Risk Management)")]
        public double RewardRiskRatio { get; set; }

        [Parameter("Max Open Trades per Symbol", DefaultValue = 1, MinValue = 1, MaxValue = 5, Group = "1. Quản Trị Vốn (Risk Management)")]
        public int MaxOpenTrades { get; set; }

        // -------------------------------------------------------------
        // PARAMETERS: Partial Take Profit & Breakeven Management
        // -------------------------------------------------------------
        [Parameter("Enable Partial TP1 at +1.5R", DefaultValue = true, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public bool EnablePartialTP { get; set; }

        [Parameter("Partial Close Volume (%)", DefaultValue = 50.0, MinValue = 10.0, MaxValue = 90.0, Step = 10.0, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public double PartialClosePercent { get; set; }

        [Parameter("Move SL to Breakeven at TP1 (+1.5R)", DefaultValue = true, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public bool EnableBreakevenAtTP1 { get; set; }

        [Parameter("Trailing Stop (ATR multiple, 0=Disable)", DefaultValue = 0.0, MinValue = 0.0, MaxValue = 5.0, Step = 0.5, Group = "2. Quản Lý Lệnh Thực Chiến (Trade Management)")]
        public double TrailingStopAtrMultiplier { get; set; }

        // -------------------------------------------------------------
        // PARAMETERS: SMC Core Engine (Structure, OB, FVG, Liquidity)
        // -------------------------------------------------------------
        [Parameter("Order Block Lookback (Bars)", DefaultValue = 30, MinValue = 10, MaxValue = 100, Group = "3. Thuật Toán SMC & Cấu Trúc Giá")]
        public int LookbackBars { get; set; }

        [Parameter("Swing High/Low Fractal Period", DefaultValue = 5, MinValue = 3, MaxValue = 15, Group = "3. Thuật Toán SMC & Cấu Trúc Giá")]
        public int FractalPeriod { get; set; }

        [Parameter("Min FVG Gap Size (Pips)", DefaultValue = 3.0, MinValue = 0.5, MaxValue = 50.0, Step = 0.5, Group = "3. Thuật Toán SMC & Cấu Trúc Giá")]
        public double MinFvgPips { get; set; }

        [Parameter("Require Liquidity Sweep / SFP", DefaultValue = true, Group = "3. Thuật Toán SMC & Cấu Trúc Giá")]
        public bool RequireLiquiditySweep { get; set; }

        // -------------------------------------------------------------
        // PARAMETERS: Indicators & Trend Filters
        // -------------------------------------------------------------
        [Parameter("Fast Trend EMA", DefaultValue = 50, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int FastEmaPeriod { get; set; }

        [Parameter("Baseline Slow EMA", DefaultValue = 200, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int SlowEmaPeriod { get; set; }

        [Parameter("ATR Period", DefaultValue = 14, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public int AtrPeriod { get; set; }

        [Parameter("ATR Buffer Multiplier for SL", DefaultValue = 1.5, MinValue = 0.5, MaxValue = 5.0, Step = 0.1, Group = "4. Bộ Lọc Xu Hướng & Biến Động")]
        public double AtrSlMultiplier { get; set; }

        // -------------------------------------------------------------
        // PARAMETERS: Session Filters & Security
        // -------------------------------------------------------------
        [Parameter("Filter Trading Hours (UTC)", DefaultValue = true, Group = "5. Phiên Giao Dịch & Bộ Lọc Spread")]
        public bool FilterTradingHours { get; set; }

        [Parameter("Start Hour UTC (London Open)", DefaultValue = 7, MinValue = 0, MaxValue = 23, Group = "5. Phiên Giao Dịch & Bộ Lọc Spread")]
        public int StartHourUtc { get; set; }

        [Parameter("End Hour UTC (NY Close)", DefaultValue = 20, MinValue = 0, MaxValue = 23, Group = "5. Phiên Giao Dịch & Bộ Lọc Spread")]
        public int EndHourUtc { get; set; }

        [Parameter("Max Allowed Spread (Pips)", DefaultValue = 3.5, MinValue = 0.5, MaxValue = 20.0, Step = 0.5, Group = "5. Phiên Giao Dịch & Bộ Lọc Spread")]
        public double MaxSpreadPips { get; set; }

        [Parameter("Custom Bot Label", DefaultValue = "TungPham_SMC", Group = "5. Phiên Giao Dịch & Bộ Lọc Spread")]
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
            Print("🚀 TÙNG PHẠM ALGO LAB - SMC cBot Initialized Successfully!");
            Print($"Asset: {SymbolName} | Timeframe: {TimeFrame} | Risk: {RiskPercent}% | R:R: 1:{RewardRiskRatio}");
            Print("==========================================================================");
        }

        protected override void OnBar()
        {
            // 1. Manage existing open positions (TP1 Partial & Breakeven)
            ManageOpenPositions();

            // 2. Check maximum open trades
            int currentOpenPositions = Positions.Count(p => p.SymbolName == SymbolName && p.Label == BotLabel);
            if (currentOpenPositions >= MaxOpenTrades)
                return;

            // 3. Spread Check
            double currentSpreadPips = (Symbol.Ask - Symbol.Bid) / Symbol.PipSize;
            if (currentSpreadPips > MaxSpreadPips)
            {
                Print($"[SMC Bot] Spread ({currentSpreadPips:F1} pips) > Max Allowed ({MaxSpreadPips:F1} pips). Skipping.");
                return;
            }

            // 4. Session Time Filter (UTC)
            if (FilterTradingHours)
            {
                int currentHour = Server.Time.Hour;
                if (currentHour < StartHourUtc || currentHour >= EndHourUtc)
                    return;
            }

            // 5. Need enough bars for SMC calculations
            if (Bars.Count < Math.Max(LookbackBars, SlowEmaPeriod) + 10)
                return;

            // 6. Execute Core SMC Analysis
            EvaluateSMCSetups();
        }

        protected override void OnTick()
        {
            // Fast tick-level check for Breakeven and Partial Close
            if (EnablePartialTP || EnableBreakevenAtTP1)
            {
                ManageOpenPositionsOnTick();
            }
        }

        // =========================================================================================
        // CORE SMC EVALUATION LOGIC
        // =========================================================================================
        private void EvaluateSMCSetups()
        {
            int lastIndex = Bars.Count - 2; // Last closed candle
            double closePrice = Bars.ClosePrices[lastIndex];
            double fastEma = _emaFast.Result[lastIndex];
            double slowEma = _emaSlow.Result[lastIndex];
            double currentAtr = _atr.Result[lastIndex];

            // -------------------------------------------------------------
            // STEP 1: MACRO TREND FILTER (EMA Alignment)
            // -------------------------------------------------------------
            bool isMacroBullish = closePrice > fastEma && fastEma >= slowEma;
            bool isMacroBearish = closePrice < fastEma && fastEma <= slowEma;

            // -------------------------------------------------------------
            // STEP 2: FIND RECENT SWING HIGHS & SWING LOWS (Liquidity Pools)
            // -------------------------------------------------------------
            double swingHigh = FindRecentSwingHigh(lastIndex, LookbackBars, FractalPeriod);
            double swingLow = FindRecentSwingLow(lastIndex, LookbackBars, FractalPeriod);

            if (swingHigh <= 0 || swingLow <= 0)
                return;

            // -------------------------------------------------------------
            // STEP 3: DETECT LIQUIDITY SWEEP / SFP (Swing Failure Pattern)
            // -------------------------------------------------------------
            bool bullishSweep = false;
            bool bearishSweep = false;

            // Check if any of recent 3 candles swept swingLow and closed back inside
            for (int i = lastIndex; i >= lastIndex - 2; i--)
            {
                if (Bars.LowPrices[i] < swingLow && Bars.ClosePrices[i] > swingLow)
                    bullishSweep = true;
                if (Bars.HighPrices[i] > swingHigh && Bars.ClosePrices[i] < swingHigh)
                    bearishSweep = true;
            }

            if (RequireLiquiditySweep)
            {
                if (isMacroBullish && !bullishSweep) isMacroBullish = false;
                if (isMacroBearish && !bearishSweep) isMacroBearish = false;
            }

            // -------------------------------------------------------------
            // STEP 4: IDENTIFY ORDER BLOCK & FVG (Fair Value Gap)
            // -------------------------------------------------------------
            // Bullish Setup Analysis
            if (isMacroBullish)
            {
                OrderBlock ob = FindBullishOrderBlock(lastIndex, LookbackBars);
                if (ob != null && ob.IsValid)
                {
                    // Check if current candle pulled back into Demand OB zone
                    double currentLow = Bars.LowPrices[lastIndex];
                    double currentClose = Bars.ClosePrices[lastIndex];

                    if (currentLow <= ob.High && currentClose >= ob.Low)
                    {
                        // Micro Trigger: Bullish candle closing green inside/above OB
                        if (Bars.ClosePrices[lastIndex] > Bars.OpenPrices[lastIndex])
                        {
                            ExecuteSMCBuyOrder(ob, currentAtr);
                        }
                    }
                }
            }
            // Bearish Setup Analysis
            else if (isMacroBearish)
            {
                OrderBlock ob = FindBearishOrderBlock(lastIndex, LookbackBars);
                if (ob != null && ob.IsValid)
                {
                    // Check if current candle pulled back into Supply OB zone
                    double currentHigh = Bars.HighPrices[lastIndex];
                    double currentClose = Bars.ClosePrices[lastIndex];

                    if (currentHigh >= ob.Low && currentClose <= ob.High)
                    {
                        // Micro Trigger: Bearish candle closing red inside/below OB
                        if (Bars.ClosePrices[lastIndex] < Bars.OpenPrices[lastIndex])
                        {
                            ExecuteSMCSellOrder(ob, currentAtr);
                        }
                    }
                }
            }
        }

        // =========================================================================================
        // ORDER EXECUTION & POSITION SIZING
        // =========================================================================================
        private void ExecuteSMCBuyOrder(OrderBlock ob, double atr)
        {
            double entryPrice = Symbol.Ask;
            // Place Stop Loss strictly below Order Block low with ATR buffer
            double stopLossPrice = ob.Low - (atr * AtrSlMultiplier);
            double riskDistance = entryPrice - stopLossPrice;

            if (riskDistance <= 0) return;

            // Target Full TP2 based on R:R
            double takeProfitPrice = entryPrice + (riskDistance * RewardRiskRatio);

            double slPips = riskDistance / Symbol.PipSize;
            double tpPips = (takeProfitPrice - entryPrice) / Symbol.PipSize;

            double volume = CalculateVolume(riskDistance);
            if (volume <= 0) return;

            string comment = $"TP_SMC_BUY_SL:{stopLossPrice:F2}_TP2:{takeProfitPrice:F2}";
            var result = ExecuteMarketOrder(TradeType.Buy, SymbolName, volume, BotLabel, slPips, tpPips, comment);

            if (result.IsSuccessful)
            {
                Print($"[SMC BUY EXECUTED] Entry: {entryPrice:F2} | SL: {stopLossPrice:F2} ({slPips:F1} pips) | TP2: {takeProfitPrice:F2} ({tpPips:F1} pips) | R:R: 1:{RewardRiskRatio} | Vol: {volume}");
            }
        }

        private void ExecuteSMCSellOrder(OrderBlock ob, double atr)
        {
            double entryPrice = Symbol.Bid;
            // Place Stop Loss strictly above Order Block high with ATR buffer
            double stopLossPrice = ob.High + (atr * AtrSlMultiplier);
            double riskDistance = stopLossPrice - entryPrice;

            if (riskDistance <= 0) return;

            // Target Full TP2 based on R:R
            double takeProfitPrice = entryPrice - (riskDistance * RewardRiskRatio);

            double slPips = riskDistance / Symbol.PipSize;
            double tpPips = (entryPrice - takeProfitPrice) / Symbol.PipSize;

            double volume = CalculateVolume(riskDistance);
            if (volume <= 0) return;

            string comment = $"TP_SMC_SELL_SL:{stopLossPrice:F2}_TP2:{takeProfitPrice:F2}";
            var result = ExecuteMarketOrder(TradeType.Sell, SymbolName, volume, BotLabel, slPips, tpPips, comment);

            if (result.IsSuccessful)
            {
                Print($"[SMC SELL EXECUTED] Entry: {entryPrice:F2} | SL: {stopLossPrice:F2} ({slPips:F1} pips) | TP2: {takeProfitPrice:F2} ({tpPips:F1} pips) | R:R: 1:{RewardRiskRatio} | Vol: {volume}");
            }
        }

        // =========================================================================================
        // DYNAMIC POSITION SIZING (Risk % Formula)
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
        // TRADE MANAGEMENT (TP1 Partial Close & Breakeven)
        // =========================================================================================
        private void ManageOpenPositions()
        {
            var openPositions = Positions.Where(p => p.SymbolName == SymbolName && p.Label == BotLabel).ToList();

            foreach (var pos in openPositions)
            {
                double initialRisk = Math.Abs(pos.EntryPrice - (pos.StopLoss ?? pos.EntryPrice));
                if (initialRisk <= 0) continue;

                // 1.5R Target price level
                double tp1Price = pos.TradeType == TradeType.Buy 
                    ? pos.EntryPrice + (initialRisk * 1.5) 
                    : pos.EntryPrice - (initialRisk * 1.5);

                bool hasReachedTP1 = pos.TradeType == TradeType.Buy 
                    ? Symbol.Bid >= tp1Price 
                    : Symbol.Ask <= tp1Price;

                // If position hit TP1 (+1.5R) and hasn't been partially closed
                if (hasReachedTP1 && !pos.Comment.Contains("[TP1_CLOSED]"))
                {
                    if (EnablePartialTP)
                    {
                        double closeUnits = Symbol.NormalizeVolumeInUnits(pos.VolumeInUnits * (PartialClosePercent / 100.0), RoundingMode.Down);
                        if (closeUnits >= Symbol.VolumeInUnitsMin && pos.VolumeInUnits - closeUnits >= Symbol.VolumeInUnitsMin)
                        {
                            ClosePosition(pos, closeUnits);
                            Print($"[TP1 HIT 🎯] Closed {PartialClosePercent}% volume ({closeUnits} units) at +1.5R profit for #{pos.Id}");
                        }
                    }

                    if (EnableBreakevenAtTP1)
                    {
                        // Move SL to Entry (Risk-Free Breakeven) + 1 pip buffer
                        double beSl = pos.TradeType == TradeType.Buy ? pos.EntryPrice + Symbol.PipSize : pos.EntryPrice - Symbol.PipSize;
                        ModifyPosition(pos, beSl, pos.TakeProfit);
                        Print($"[BREAKEVEN SHIELD 🛡] Stop Loss moved to Entry {beSl:F2} for #{pos.Id}. Trade is now 100% RISK-FREE!");
                    }

                    ModifyPosition(pos, pos.StopLoss, pos.TakeProfit);
                }
            }
        }

        private void ManageOpenPositionsOnTick()
        {
            ManageOpenPositions();
        }

        // =========================================================================================
        // SMC HELPER ALGORITHMS: Fractals, Order Blocks, FVGs
        // =========================================================================================
        private double FindRecentSwingHigh(int startIndex, int lookback, int period)
        {
            for (int i = startIndex - period; i >= startIndex - lookback; i--)
            {
                if (i - period < 0 || i + period >= Bars.Count) continue;
                double candidate = Bars.HighPrices[i];
                bool isSwing = true;
                for (int j = 1; j <= period; j++)
                {
                    if (Bars.HighPrices[i - j] >= candidate || Bars.HighPrices[i + j] > candidate)
                    {
                        isSwing = false;
                        break;
                    }
                }
                if (isSwing) return candidate;
            }
            return Bars.HighPrices[startIndex];
        }

        private double FindRecentSwingLow(int startIndex, int lookback, int period)
        {
            for (int i = startIndex - period; i >= startIndex - lookback; i--)
            {
                if (i - period < 0 || i + period >= Bars.Count) continue;
                double candidate = Bars.LowPrices[i];
                bool isSwing = true;
                for (int j = 1; j <= period; j++)
                {
                    if (Bars.LowPrices[i - j] <= candidate || Bars.LowPrices[i + j] < candidate)
                    {
                        isSwing = false;
                        break;
                    }
                }
                if (isSwing) return candidate;
            }
            return Bars.LowPrices[startIndex];
        }

        private OrderBlock FindBullishOrderBlock(int startIndex, int lookback)
        {
            double minFvgPriceGap = MinFvgPips * Symbol.PipSize;

            for (int i = startIndex - 1; i >= startIndex - lookback; i--)
            {
                if (i - 1 < 0 || i + 2 >= Bars.Count) continue;

                // Bullish Imbalance / FVG: High of Candle 1 < Low of Candle 3
                double candle1High = Bars.HighPrices[i];
                double candle3Low = Bars.LowPrices[i + 2];

                if (candle3Low - candle1High >= minFvgPriceGap)
                {
                    // The last opposing bearish candle before expansion is the Order Block
                    for (int k = i; k >= i - 3 && k >= 0; k--)
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

        private OrderBlock FindBearishOrderBlock(int startIndex, int lookback)
        {
            double minFvgPriceGap = MinFvgPips * Symbol.PipSize;

            for (int i = startIndex - 1; i >= startIndex - lookback; i--)
            {
                if (i - 1 < 0 || i + 2 >= Bars.Count) continue;

                // Bearish Imbalance / FVG: Low of Candle 1 > High of Candle 3
                double candle1Low = Bars.LowPrices[i];
                double candle3High = Bars.HighPrices[i + 2];

                if (candle1Low - candle3High >= minFvgPriceGap)
                {
                    // The last opposing bullish candle before expansion is the Order Block
                    for (int k = i; k >= i - 3 && k >= 0; k--)
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
