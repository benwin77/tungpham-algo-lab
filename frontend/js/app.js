/**
 * SMC & PA WEEKLY TRADING TERMINAL - FRONTEND APPLICATION
 */

const API_BASE = ""; // Relative path to FastAPI backend

// Application Global State
const STATE = {
    activePair: "XAUUSD",
    forecasts: {},
    marketData: {},
    calendar: [],
    news: [],
    trackRecord: { stats: {}, records: [] },
    quantLab: [],
    tradingViewWidget: null,
    isAdmin: false,
    adminToken: localStorage.getItem("tp_admin_token") || ""
};

// DOM Elements Cache
const DOM = {
    // Header & Ticker
    systemStatus: document.getElementById("system-status"),
    tickerContainer: document.getElementById("ticker-items-container"),
    assetGrid: document.getElementById("asset-cards-grid"),
    btnRefreshAll: document.getElementById("btn-refresh-all"),
    refreshIcon: document.getElementById("refresh-icon"),
    btnExportText: document.getElementById("btn-export-text"),
    btnAdminAuth: document.getElementById("btn-admin-auth"),
    adminBtnText: document.getElementById("admin-btn-text"),

    // Active Pair View
    symbolBadge: document.getElementById("detail-symbol-badge"),
    assetName: document.getElementById("detail-asset-name"),
    strategyBadge: document.getElementById("detail-strategy-badge"),
    statusBadge: document.getElementById("detail-status-badge"),
    customBadge: document.getElementById("detail-custom-badge"),
    biasBanner: document.getElementById("detail-bias-banner"),
    signalDir: document.getElementById("detail-signal-dir"),
    structureSub: document.getElementById("detail-structure-sub"),
    rrValue: document.getElementById("detail-rr-value"),

    // Structure Pipeline
    sfD1: document.getElementById("sf-d1"),
    sfH4: document.getElementById("sf-h4"),
    sfH1: document.getElementById("sf-h1"),
    sfM15: document.getElementById("sf-m15"),

    // Execution & PRO Gating
    gatedWrapper: document.getElementById("execution-gated-wrapper"),
    entryVal: document.getElementById("detail-entry-val"),
    slVal: document.getElementById("detail-sl-val"),
    tp1Val: document.getElementById("detail-tp1-val"),
    tp2Val: document.getElementById("detail-tp2-val"),
    triggerBadge: document.getElementById("detail-trigger-badge"),
    triggerDesc: document.getElementById("detail-trigger-desc"),

    // SMC Zones
    obVal: document.getElementById("detail-ob-val"),
    bslVal: document.getElementById("detail-bsl-val"),
    sslVal: document.getElementById("detail-ssl-val"),
    srVal: document.getElementById("detail-sr-val"),

    // Checklist & Rationale
    checklistContainer: document.getElementById("detail-checklist-items"),
    rationaleText: document.getElementById("detail-rationale-text"),
    userNotesBox: document.getElementById("detail-user-notes-box"),
    userNotesText: document.getElementById("detail-user-notes-text"),

    // Actions
    btnOpenEditModal: document.getElementById("btn-open-edit-modal"),
    btnResetScenario: document.getElementById("btn-reset-scenario"),

    // Chart
    chartPairName: document.getElementById("chart-pair-name"),
    tvContainer: document.getElementById("tradingview_chart"),

    // Sidebar & Tabs
    tabButtons: document.querySelectorAll(".tab-btn"),
    tabPanes: document.querySelectorAll(".tab-pane"),
    calendarList: document.getElementById("calendar-list"),
    calendarImpactFilter: document.getElementById("calendar-impact-filter"),
    newsList: document.getElementById("news-list"),
    newsSentPair: document.getElementById("news-sent-pair"),
    newsSentScore: document.getElementById("news-sent-score"),
    newsBarBull: document.getElementById("news-bar-bull"),
    newsBarBear: document.getElementById("news-bar-bear"),
    newsBullVal: document.getElementById("news-bull-val"),
    newsBearVal: document.getElementById("news-bear-val"),
    matrixTbody: document.getElementById("matrix-tbody"),

    // Track Record elements
    trTotalSetups: document.getElementById("tr-total-setups"),
    trWinRate: document.getElementById("tr-win-rate"),
    trNetR: document.getElementById("tr-net-r"),
    trProfitFactor: document.getElementById("tr-profit-factor"),
    trAvgWin: document.getElementById("tr-avg-win"),
    trAvgLoss: document.getElementById("tr-avg-loss"),
    trMaxStreak: document.getElementById("tr-max-streak"),
    trackRecordList: document.getElementById("track-record-list"),

    // Quant Lab elements
    quantStrategiesList: document.getElementById("quant-strategies-list"),

    // Edit Modal
    editModal: document.getElementById("edit-modal-overlay"),
    btnCloseModal: document.getElementById("btn-close-modal"),
    btnCancelModal: document.getElementById("btn-cancel-modal"),
    editForm: document.getElementById("edit-scenario-form"),
    modalPairName: document.getElementById("modal-pair-name"),
    modalInputPair: document.getElementById("modal-input-pair"),
    modalSelectBias: document.getElementById("modal-select-bias"),
    modalSelectStatus: document.getElementById("modal-select-status"),
    modalInputTrigger: document.getElementById("modal-input-trigger"),
    modalInputEntry: document.getElementById("modal-input-entry"),
    modalInputSl: document.getElementById("modal-input-sl"),
    modalInputTp1: document.getElementById("modal-input-tp1"),
    modalInputTp2: document.getElementById("modal-input-tp2"),
    modalChecklistEditor: document.getElementById("modal-checklist-editor"),
    modalInputRationale: document.getElementById("modal-input-rationale"),
    modalInputNotes: document.getElementById("modal-input-notes"),
    btnTriggerTelegramAlert: document.getElementById("btn-trigger-telegram-alert"),

    // Export Modal
    exportModal: document.getElementById("export-modal-overlay"),
    btnCloseExport: document.getElementById("btn-close-export"),
    exportTextArea: document.getElementById("export-text-area"),
    btnCopyExport: document.getElementById("btn-copy-export"),
    copyBtnText: document.getElementById("copy-btn-text"),

    // Login Modal
    loginModal: document.getElementById("login-modal-overlay"),
    btnCloseLogin: document.getElementById("btn-close-login"),
    btnCancelLogin: document.getElementById("btn-cancel-login"),
    loginForm: document.getElementById("login-form"),
    adminPasswordInput: document.getElementById("admin-password-input"),

    // Toasts
    toastContainer: document.getElementById("toast-container")
};

let pendingAdminAction = null;

// Toast Notifications Helper
function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "fa-circle-check text-success" : (type === "warning" ? "fa-triangle-exclamation text-warning" : "fa-circle-info text-primary");
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    DOM.toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// -------------------------------------------------------------
// Auth & Permission Management
// -------------------------------------------------------------

async function initAuth() {
    if (STATE.adminToken) {
        try {
            const res = await fetch(`${API_BASE}/api/auth/verify`, {
                headers: { "X-Admin-Token": STATE.adminToken }
            });
            if (res.ok) {
                const data = await res.json();
                if (data.authenticated) {
                    STATE.isAdmin = true;
                } else {
                    STATE.isAdmin = false;
                    STATE.adminToken = "";
                    localStorage.removeItem("tp_admin_token");
                }
            }
        } catch (e) {
            console.warn("Auth check failed:", e);
        }
    }
    updateAdminUI();
}

function updateAdminUI() {
    if (STATE.isAdmin) {
        document.body.classList.add("admin-authenticated");
        DOM.btnAdminAuth.classList.add("logged-in");
        DOM.btnAdminAuth.innerHTML = `<i class="fa-solid fa-crown text-gold"></i> <span id="admin-btn-text">Mr Tung (Admin)</span>`;
        DOM.btnAdminAuth.title = "Nhấp để đăng xuất";
    } else {
        document.body.classList.remove("admin-authenticated");
        DOM.btnAdminAuth.classList.remove("logged-in");
        DOM.btnAdminAuth.innerHTML = `<i class="fa-solid fa-lock"></i> <span id="admin-btn-text">Admin Login</span>`;
        DOM.btnAdminAuth.title = "Dành riêng cho Mr Tung";
    }
}

function openLoginModal(actionCallback = null) {
    pendingAdminAction = actionCallback;
    DOM.adminPasswordInput.value = "";
    DOM.loginModal.classList.add("active");
    DOM.adminPasswordInput.focus();
}

function closeLoginModal() {
    DOM.loginModal.classList.remove("active");
    pendingAdminAction = null;
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const pwd = DOM.adminPasswordInput.value.trim();
    if (!pwd) return;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pwd })
        });

        if (res.ok) {
            const data = await res.json();
            STATE.isAdmin = true;
            STATE.adminToken = data.token;
            localStorage.setItem("tp_admin_token", data.token);
            updateAdminUI();
            closeLoginModal();
            showToast("Chào mừng Mr Tung! Đã mở quyền chỉnh sửa kịch bản.", "success");

            if (typeof pendingAdminAction === "function") {
                const action = pendingAdminAction;
                pendingAdminAction = null;
                action();
            }
        } else {
            showToast("Mật khẩu không chính xác! Vui lòng thử lại.", "warning");
        }
    } catch (err) {
        showToast("Lỗi kết nối máy chủ xác thực.", "warning");
    }
}

function handleAdminButtonClick() {
    if (STATE.isAdmin) {
        if (confirm("Mr Tung có muốn đăng xuất quyền Admin và chuyển về chế độ Khách (Chỉ xem)?")) {
            STATE.isAdmin = false;
            STATE.adminToken = "";
            localStorage.removeItem("tp_admin_token");
            updateAdminUI();
            showToast("Đã đăng xuất quyền Admin.", "info");
        }
    } else {
        openLoginModal();
    }
}

// -------------------------------------------------------------
// Visitor Tracking & Analytics
// -------------------------------------------------------------

function getOrCreateClientId() {
    let cid = localStorage.getItem("tp_client_id");
    if (!cid) {
        cid = "tp_cid_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now().toString(36);
        localStorage.setItem("tp_client_id", cid);
    }
    return cid;
}

function updateAnalyticsDisplay(stats) {
    if (!stats) return;
    const formatNum = n => (n !== undefined && n !== null) ? Number(n).toLocaleString("vi-VN") : "--";
    
    // Header
    const hOnline = document.getElementById("header-online-count");
    if (hOnline) hOnline.textContent = formatNum(stats.online_now);
    const hViews = document.getElementById("header-views-count");
    if (hViews) hViews.textContent = formatNum(stats.total_views);

    // Footer
    const sUnique = document.getElementById("stat-unique-visitors");
    if (sUnique) sUnique.textContent = formatNum(stats.unique_visitors);
    const sTotal = document.getElementById("stat-total-views");
    if (sTotal) sTotal.textContent = formatNum(stats.total_views);
    const sToday = document.getElementById("stat-today-views");
    if (sToday) sToday.textContent = formatNum(stats.today_views);
    const sOnline = document.getElementById("stat-online-now");
    if (sOnline) sOnline.textContent = formatNum(stats.online_now);
}

async function trackVisitorPresence(isPageview = false) {
    try {
        const cid = getOrCreateClientId();
        const res = await fetch(`${API_BASE}/api/analytics/track`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ client_id: cid, is_pageview: isPageview })
        });
        if (res.ok) {
            const stats = await res.json();
            updateAnalyticsDisplay(stats);
        }
    } catch (e) {
        // silent failover
    }
}

// -------------------------------------------------------------
// API Calls & Data Ingestion
// -------------------------------------------------------------

let realtimeStreamStarted = false;

async function initDashboard() {
    try {
        trackVisitorPresence(true); // Track pageview on load
        
        await Promise.all([
            loadMarketData(),
            loadForecasts(),
            loadCalendar(),
            loadNews(),
            loadTrackRecord(),
            loadQuantLab()
        ]);
        renderAll();
        if (!realtimeStreamStarted) {
            realtimeStreamStarted = true;
            startRealtimeTickerStream();
            setInterval(() => trackVisitorPresence(false), 30000); // 30s heartbeat
        }
    } catch (err) {
        console.error("Init dashboard error:", err);
        showToast("Đang kết nối backend server...", "info");
    }
}

function startRealtimeTickerStream() {
    // 1. Live Binance stream for BTCUSD (Polls every 3s direct from Binance 24/7)
    async function updateLiveBTC() {
        try {
            const res = await fetch("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT");
            if (res.ok) {
                const data = await res.json();
                const price = parseFloat(data.lastPrice).toFixed(2);
                const chg = parseFloat(data.priceChangePercent).toFixed(2);
                if (!STATE.marketData["BTCUSD"]) {
                    STATE.marketData["BTCUSD"] = {};
                }
                STATE.marketData["BTCUSD"].current_price = parseFloat(price);
                STATE.marketData["BTCUSD"].change_pct = parseFloat(chg);

                renderTickerRibbon();
                
                // Update active BTC card price & detail if active
                const btcCard = document.querySelector(".asset-card:nth-child(2) .ac-price");
                if (btcCard) btcCard.textContent = price;
                
                if (STATE.activePair === "BTCUSD") {
                    const priceSub = document.querySelector(".detail-stat-card .stat-val");
                    if (priceSub) priceSub.textContent = price;
                }
            }
        } catch (e) {
            // silent fallback
        }
    }

    // 2. Poll backend market-data every 4s for Forex, Gold & US100
    async function updateLiveMarket() {
        try {
            const res = await fetch(`${API_BASE}/api/market-data`);
            if (res.ok) {
                const data = await res.json();
                Object.assign(STATE.marketData, data);
                renderTickerRibbon();
                renderAssetGrid();

                // Update active pair detail if available
                const activeM = data[STATE.activePair];
                if (activeM && activeM.current_price !== undefined) {
                    const priceSub = document.querySelector(".detail-stat-card .stat-val");
                    if (priceSub) priceSub.textContent = activeM.current_price;
                }
            }
        } catch (e) {
            // silent fallback
        }
    }

    updateLiveBTC();
    updateLiveMarket();
    setInterval(updateLiveBTC, 3000);
    setInterval(updateLiveMarket, 4000);
}

async function loadMarketData() {
    try {
        const res = await fetch(`${API_BASE}/api/market-data`);
        if (res.ok) {
            STATE.marketData = await res.json();
        }
    } catch (e) {
        console.warn("Failed loading market data:", e);
    }
}

async function loadForecasts() {
    try {
        const res = await fetch(`${API_BASE}/api/forecasts`);
        if (res.ok) {
            STATE.forecasts = await res.json();
        }
    } catch (e) {
        console.warn("Failed loading forecasts:", e);
    }
}

async function loadCalendar() {
    try {
        const impact = DOM.calendarImpactFilter.value;
        const res = await fetch(`${API_BASE}/api/calendar?impact=${impact}`);
        if (res.ok) {
            STATE.calendar = await res.json();
        }
    } catch (e) {
        console.warn("Failed loading calendar:", e);
    }
}

async function loadNews() {
    try {
        const res = await fetch(`${API_BASE}/api/news`);
        if (res.ok) {
            STATE.news = await res.json();
        }
    } catch (e) {
        console.warn("Failed loading news:", e);
    }
}

async function loadTrackRecord() {
    try {
        const res = await fetch(`${API_BASE}/api/track-record`);
        if (res.ok) {
            STATE.trackRecord = await res.json();
        }
    } catch (e) {
        console.warn("Failed loading track record:", e);
    }
}

async function loadQuantLab() {
    try {
        const res = await fetch(`${API_BASE}/api/quant-lab`);
        if (res.ok) {
            const data = await res.json();
            STATE.quantLab = data.strategies || [];
        }
    } catch (e) {
        console.warn("Failed loading quant lab:", e);
    }
}

async function refreshAllData() {
    DOM.refreshIcon.classList.add("fa-spin");
    try {
        showToast("Đang thu thập tin tức & phân tích lại thị trường...", "info");
        const res = await fetch(`${API_BASE}/api/refresh`, { method: "POST" });
        if (res.ok) {
            await initDashboard();
            showToast("Đã cập nhật dữ liệu & kịch bản mới nhất!", "success");
        }
    } catch (e) {
        showToast("Lỗi khi làm mới dữ liệu.", "warning");
    } finally {
        DOM.refreshIcon.classList.remove("fa-spin");
    }
}

// -------------------------------------------------------------
// UI Rendering Functions
// -------------------------------------------------------------

function renderAll() {
    renderTickerRibbon();
    renderAssetGrid();
    renderActivePairDetail();
    renderTradingViewWidget();
    renderCalendar();
    renderNews();
    renderTrackRecord();
    renderQuantLab();
    renderMatrixTable();
}

function renderTickerRibbon() {
    const pairs = ["XAUUSD", "BTCUSD", "US100", "GBPUSD", "USDJPY", "CADCHF"];
    DOM.tickerContainer.innerHTML = pairs.map(p => {
        const data = STATE.marketData[p] || {};
        const price = data.current_price !== undefined ? data.current_price : "--";
        const chg = data.change_pct || 0;
        const chgClass = chg >= 0 ? "t-up" : "t-down";
        const chgSign = chg >= 0 ? "+" : "";
        const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD" : (p === "US100" ? "US100" : `${p.slice(0,3)}/${p.slice(3)}`));
        return `
            <div class="ticker-item" onclick="switchPair('${p}')">
                <span class="t-name">${formattedPair}:</span>
                <span class="t-price">${price}</span>
                <span class="${chgClass}">(${chgSign}${chg}%)</span>
            </div>
        `;
    }).join("");
}

function renderAssetGrid() {
    const pairs = ["XAUUSD", "BTCUSD", "US100", "GBPUSD", "USDJPY", "CADCHF"];
    DOM.assetGrid.innerHTML = pairs.map(p => {
        const f = STATE.forecasts[p] || {};
        const m = STATE.marketData[p] || {};
        const isActive = p === STATE.activePair ? "active" : "";
        const isGold = p === "XAUUSD" ? "gold-card" : "";
        const bias = f.bias || "WAIT";
        const biasClass = bias.toLowerCase();
        const biasBadge = bias === "BUY" ? "🟢 BUY" : (bias === "SELL" ? "🔴 SELL" : "⚪️ WAIT");
        const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD" : (p === "US100" ? "US100" : `${p.slice(0,3)}/${p.slice(3)}`));

        return `
            <div class="asset-card ${isGold} ${isActive}" onclick="switchPair('${p}')">
                <div class="ac-top">
                    <span class="ac-pair">${formattedPair}</span>
                    <span class="ac-bias-pill ${biasClass}">${biasBadge}</span>
                </div>
                <div class="ac-price">${m.current_price || f.current_price || "--"}</div>
                <div class="ac-sub">
                    <span>${f.status || "PLANNING"}</span>
                    <span class="ac-rr">R:R ${f.rr_ratio || "1:3"}</span>
                </div>
            </div>
        `;
    }).join("");
}

function renderActivePairDetail() {
    const p = STATE.activePair;
    const f = STATE.forecasts[p] || {};
    const m = STATE.marketData[p] || {};
    const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD (24/7)" : (p === "US100" ? "US100 (Nasdaq)" : `${p.slice(0,3)}/${p.slice(3)}`));

    DOM.symbolBadge.textContent = formattedPair;
    if (p === "XAUUSD") {
        DOM.symbolBadge.classList.add("gold");
    } else {
        DOM.symbolBadge.classList.remove("gold");
    }

    DOM.assetName.textContent = m.name || f.name || formattedPair;
    DOM.strategyBadge.textContent = f.strategy_type || "SMC + Thuần PA + Trend Follow";
    
    // Lifecycle Status Badge
    const st = f.status || "WAITING";
    let stBadge = "🟡 WAITING";
    if (st === "ACTIVE") stBadge = "🟢 ACTIVE";
    else if (st === "TP1_HIT") stBadge = "✅ TP1 HIT";
    else if (st === "TP2_HIT") stBadge = "🏆 TP2 HIT";
    else if (st === "INVALIDATED") stBadge = "❌ INVALIDATED";
    DOM.statusBadge.textContent = stBadge;

    DOM.customBadge.style.display = f.user_customized ? "inline-block" : "none";

    // Structure Pipeline Flow
    const flow = f.market_structure_flow || {};
    if (DOM.sfD1) DOM.sfD1.textContent = flow.d1 || (f.bias === "BUY" ? "BULLISH" : "BEARISH");
    if (DOM.sfH4) DOM.sfH4.textContent = flow.h4 || (f.bias === "BUY" ? "BULLISH BOS" : "BEARISH CHOCH");
    if (DOM.sfH1) DOM.sfH1.textContent = flow.h1 || "PULLBACK DISCOUNT";
    if (DOM.sfM15) DOM.sfM15.textContent = flow.m15 || "TRIGGER CONFIRM";

    // Bias Banner
    const isSell = f.bias === "SELL";
    if (isSell) {
        DOM.biasBanner.classList.add("sell-banner");
    } else {
        DOM.biasBanner.classList.remove("sell-banner");
    }
    DOM.signalDir.textContent = f.bias === "BUY" ? "🟢 BUY SETUP" : (f.bias === "SELL" ? "🔴 SELL SETUP" : "⚪️ WAIT SETUP");
    DOM.structureSub.textContent = f.structure || "MARKET STRUCTURE ANALYSIS";
    DOM.rrValue.textContent = f.rr_ratio || "1:2.5";

    // Levels
    DOM.entryVal.textContent = f.entry_zone || "--";
    DOM.slVal.textContent = f.stop_loss || "--";
    DOM.tp1Val.textContent = f.tp1 || "--";
    DOM.tp2Val.textContent = f.tp2 || "--";

    // Execution Trigger Card
    if (DOM.triggerBadge) DOM.triggerBadge.textContent = stBadge;
    if (DOM.triggerDesc) DOM.triggerDesc.textContent = f.trigger || (f.bias === "BUY" ? "M15 Bullish CHOCH + displacement nến xác nhận + retest Order Block" : "M15 Bearish CHOCH + râu quét thanh khoản đỉnh + retest Supply Zone");

    // SMC Key Zones
    DOM.obVal.textContent = f.ob_zone || "--";
    DOM.bslVal.textContent = f.bsl || "--";
    DOM.sslVal.textContent = f.ssl || "--";
    DOM.srVal.textContent = f.key_sr || "--";

    // Checklist
    const checklist = f.checklist || [];
    DOM.checklistContainer.innerHTML = checklist.map(item => `
        <div class="check-item">
            <i class="fa-solid ${item.checked ? 'fa-square-check text-success' : 'fa-square text-dim'}"></i>
            <span>${item.text}</span>
        </div>
    `).join("") || "<span class='text-dim'>Chưa có tiêu chí</span>";

    // Rationale & Notes
    DOM.rationaleText.textContent = f.rationale || "Đang cập nhật phân tích...";
    if (f.user_notes) {
        DOM.userNotesBox.style.display = "block";
        DOM.userNotesText.textContent = f.user_notes;
    } else {
        DOM.userNotesBox.style.display = "none";
    }

    // Chart header title
    const chartLabel = (p === "XAUUSD") ? "XAU/USD (Spot Gold)" : ((p === "BTCUSD") ? "BTC/USD (Bitcoin 24/7)" : ((p === "US100") ? "US100 (Nasdaq 100 Index)" : formattedPair));
    DOM.chartPairName.textContent = `Biểu Đồ Trực Tiếp: ${chartLabel}`;
}

function renderTrackRecord() {
    const stats = STATE.trackRecord.stats || {};
    const records = STATE.trackRecord.records || [];

    if (DOM.trTotalSetups) DOM.trTotalSetups.textContent = stats.total_setups || "0";
    if (DOM.trWinRate) DOM.trWinRate.textContent = `${stats.win_rate || 0}%`;
    if (DOM.trNetR) DOM.trNetR.textContent = stats.net_r || "+0.0R";
    if (DOM.trProfitFactor) DOM.trProfitFactor.textContent = stats.profit_factor || "0.0";
    if (DOM.trAvgWin) DOM.trAvgWin.textContent = stats.avg_winner || "+0.0R";
    if (DOM.trAvgLoss) DOM.trAvgLoss.textContent = stats.avg_loser || "-0.0R";
    if (DOM.trMaxStreak) DOM.trMaxStreak.textContent = stats.max_losing_streak || "0";

    if (!DOM.trackRecordList) return;
    DOM.trackRecordList.innerHTML = records.map(r => {
        const isWin = r.result === "WIN";
        const isLoss = r.result === "LOSS";
        const pillClass = isWin ? "win" : (isLoss ? "loss" : "be");
        const formattedPair = r.pair === "XAUUSD" ? "XAU/USD" : (r.pair === "BTCUSD" ? "BTC/USD" : (r.pair === "US100" ? "US100" : `${r.pair.slice(0,3)}/${r.pair.slice(3)}`));
        const dirIcon = r.direction === "BUY" ? "🟢 BUY" : "🔴 SELL";

        return `
            <div class="tr-card">
                <div class="tr-top-row">
                    <div class="tr-pair-badge">${formattedPair} • ${dirIcon} <span class="text-dim" style="font-weight:400; font-size:0.68rem;">(${r.date})</span></div>
                    <span class="tr-res-pill ${pillClass}">${r.r_multiple}</span>
                </div>
                <div class="tr-strat-text"><i class="fa-solid fa-crosshairs text-gold"></i> ${r.strategy || "SMC Strategy"}</div>
                <div class="tr-levels-row">
                    <span>Entry: <strong>${r.entry}</strong></span>
                    <span>SL: <strong>${r.sl}</strong></span>
                    <span>TP: <strong>${r.tp}</strong></span>
                </div>
                <div class="tr-notes">${r.notes || ""}</div>
            </div>
        `;
    }).join("");
}

function renderQuantLab() {
    if (!DOM.quantStrategiesList) return;
    DOM.quantStrategiesList.innerHTML = (STATE.quantLab || []).map(s => {
        return `
            <div class="quant-strat-card">
                <div class="qs-header">
                    <div class="qs-title-group">
                        <h5>${s.name}</h5>
                        <span class="qs-market"><i class="fa-solid fa-chart-pie text-gold"></i> ${s.market} • ${s.timeframe}</span>
                    </div>
                    <span class="qs-badge">${s.badge || "PRO ALGO"}</span>
                </div>
                <div class="qs-metrics-grid">
                    <div class="qm-box">
                        <span class="qm-label">WIN RATE</span>
                        <strong class="qm-val text-success">${s.win_rate}</strong>
                    </div>
                    <div class="qm-box">
                        <span class="qm-label">PROFIT FACTOR</span>
                        <strong class="qm-val text-gold">${s.profit_factor}</strong>
                    </div>
                    <div class="qm-box">
                        <span class="qm-label">MAX DRAWDOWN</span>
                        <strong class="qm-val text-danger">${s.max_drawdown}</strong>
                    </div>
                    <div class="qm-box">
                        <span class="qm-label">EXPECTANCY</span>
                        <strong class="qm-val text-primary">${s.expectancy}</strong>
                    </div>
                </div>
                <p class="qs-desc">${s.description}</p>
            </div>
        `;
    }).join("");
}

function renderTradingViewWidget() {
    const p = STATE.activePair;
    let tvSymbol = "OANDA:XAUUSD";
    if (p === "XAUUSD") tvSymbol = "OANDA:XAUUSD";
    else if (p === "BTCUSD") tvSymbol = "BINANCE:BTCUSDT";
    else if (p === "US100") tvSymbol = "PEPPERSTONE:NAS100";
    else if (p === "GBPUSD") tvSymbol = "FX:GBPUSD";
    else if (p === "USDJPY") tvSymbol = "FX:USDJPY";
    else if (p === "CADCHF") tvSymbol = "FX:CADCHF";

    const container = document.getElementById("tradingview_chart");
    if (!container) return;
    container.innerHTML = "";

    function loadWidget() {
        if (typeof TradingView !== "undefined" && TradingView.widget) {
            new TradingView.widget({
                "autosize": true,
                "symbol": tvSymbol,
                "interval": "240",
                "timezone": "Asia/Ho_Chi_Minh",
                "theme": "dark",
                "style": "1",
                "locale": "vi_VN",
                "toolbar_bg": "#0b0c10",
                "enable_publishing": false,
                "hide_side_toolbar": false,
                "allow_symbol_change": true,
                "studies": [
                    "MASimple@tv-basicstudies",
                    "EMA@tv-basicstudies",
                    "RSI@tv-basicstudies"
                ],
                "container_id": "tradingview_chart"
            });
        } else {
            // Fallback iframe embed
            const encodedSym = encodeURIComponent(tvSymbol);
            container.innerHTML = `
                <iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_chart&symbol=${encodedSym}&interval=240&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=%5B%22MASimple%40tv-basicstudies%22%2C%22EMA%40tv-basicstudies%22%2C%22RSI%40tv-basicstudies%22%5D&theme=dark&style=1&timezone=Asia%2FHo_Chi_Minh&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=vi_VN&utm_source=localhost" style="width: 100%; height: 100%; border: none;"></iframe>
            `;
        }
    }

    loadWidget();
}

function renderCalendar() {
    const rawEvents = STATE.calendar || [];
    if (rawEvents.length === 0) {
        DOM.calendarList.innerHTML = "<div class='text-dim text-center py-4'>Không có sự kiện kinh tế phù hợp</div>";
        return;
    }

    // Sort strictly chronologically from Monday to Friday/Sunday
    const sortedEvents = [...rawEvents].sort((a, b) => {
        const timeA = a.date ? new Date(a.date).getTime() : 0;
        const timeB = b.date ? new Date(b.date).getTime() : 0;
        return timeA - timeB;
    });

    let currentDayGroup = null;
    let htmlOutput = "";

    sortedEvents.forEach(e => {
        const dayLabel = e.day_vn || "Trong tuần";
        
        // Insert day header when day changes
        if (dayLabel !== currentDayGroup) {
            currentDayGroup = dayLabel;
            htmlOutput += `
                <div class="cal-day-divider">
                    <i class="fa-solid fa-calendar-day"></i>
                    <span>${dayLabel.toUpperCase()}</span>
                </div>
            `;
        }

        const impactClass = `impact-${(e.impact || "low").toLowerCase()}`;
        const timePeriod = e.period ? `${e.time_vn || ""} (${e.period})` : (e.time_vn || e.date || "");
        
        htmlOutput += `
            <div class="cal-event-card">
                <div class="cal-top">
                    <div class="cal-tag-group">
                        <span class="cal-currency">${e.currency || "USD"}</span>
                        <span class="cal-datetime-tag"><i class="fa-regular fa-clock"></i> ${timePeriod}</span>
                    </div>
                    <span class="cal-impact-badge ${impactClass}">${e.impact} Impact</span>
                </div>
                <div class="cal-title">${e.title}</div>
                <div class="cal-stats">
                    <span>Dự báo: <strong>${e.forecast || "--"}</strong></span>
                    <span>Trước: <strong>${e.previous || "--"}</strong></span>
                    ${e.actual && e.actual !== "--" ? `<span>Thực tế: <strong style="color:#10b981;">${e.actual}</strong></span>` : ""}
                </div>
            </div>
        `;
    });

    DOM.calendarList.innerHTML = htmlOutput;
}

function renderNews() {
    const p = STATE.activePair;
    const allNews = STATE.news || [];
    const relevantNews = allNews.filter(n => (n.pairs || []).includes(p) || (n.pairs || []).includes("ALL"));
    const displayNews = relevantNews.length ? relevantNews : allNews;

    const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD" : (p === "US100" ? "US100" : `${p.slice(0,3)}/${p.slice(3)}`));
    DOM.newsSentPair.textContent = formattedPair;

    // Sentiment Gauge calculations
    const f = STATE.forecasts[p] || {};
    const bullPct = f.bull_score !== undefined ? f.bull_score : 65;
    const bearPct = 100 - bullPct;
    DOM.newsSentScore.textContent = `${bullPct}% BULLISH`;
    DOM.newsBarBull.style.width = `${bullPct}%`;
    DOM.newsBarBear.style.width = `${bearPct}%`;
    DOM.newsBullVal.textContent = `${bullPct}%`;
    DOM.newsBearVal.textContent = `${bearPct}%`;

    if (displayNews.length === 0) {
        DOM.newsList.innerHTML = "<div class='text-dim text-center py-4'>Chưa có tin tức mới</div>";
        return;
    }

    DOM.newsList.innerHTML = displayNews.map(n => `
        <div class="news-item-card">
            <div class="news-meta-row">
                <span class="news-source">${n.source}</span>
                <span>${n.published ? n.published.slice(0, 16) : ""}</span>
            </div>
            <div class="news-title">
                <a href="${n.url}" target="_blank" style="color:inherit; text-decoration:none;">${n.title}</a>
            </div>
            <div class="news-summary">${n.summary}</div>
        </div>
    `).join("");
}

function renderMatrixTable() {
    const pairs = ["XAUUSD", "BTCUSD", "US100", "GBPUSD", "USDJPY", "CADCHF"];
    DOM.matrixTbody.innerHTML = pairs.map(p => {
        const f = STATE.forecasts[p] || {};
        const biasBadge = f.bias === "BUY" ? "<span class='text-success'>🟢 BUY</span>" : (f.bias === "SELL" ? "<span class='text-danger'>🔴 SELL</span>" : "⚪️ WAIT");
        const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD" : (p === "US100" ? "US100" : `${p.slice(0,3)}/${p.slice(3)}`));

        return `
            <tr onclick="switchPair('${p}')" style="cursor:pointer;">
                <td style="font-weight:700; color:#fff;">${formattedPair}</td>
                <td>${biasBadge}</td>
                <td style="color:#d1d5db;">${f.entry_zone || "--"}</td>
                <td class="text-danger">${f.stop_loss || "--"}</td>
                <td style="color:#e5e7eb;">${f.tp1 || "--"} / <span>${f.tp2 || "--"}</span></td>
                <td style="color:#10b981; font-weight:700;">${f.rr_ratio || "1:2.5"}</td>
            </tr>
        `;
    }).join("");
}

// -------------------------------------------------------------
// User Interactions & Modal Handlers
// -------------------------------------------------------------

function switchPair(pairKey) {
    if (STATE.activePair === pairKey) return;
    STATE.activePair = pairKey;
    renderAssetGrid();
    renderActivePairDetail();
    renderTradingViewWidget();
    renderNews();
}

function openEditModal() {
    if (!STATE.isAdmin) {
        showToast("Vui lòng đăng nhập mật khẩu Admin (Mr Tung) để chỉnh sửa kịch bản!", "info");
        openLoginModal(openEditModal);
        return;
    }

    const p = STATE.activePair;
    const f = STATE.forecasts[p] || {};
    const formattedPair = p === "XAUUSD" ? "XAU/USD" : (p === "BTCUSD" ? "BTC/USD" : (p === "US100" ? "US100" : `${p.slice(0,3)}/${p.slice(3)}`));

    DOM.modalPairName.textContent = formattedPair;
    DOM.modalInputPair.value = p;
    DOM.modalSelectBias.value = f.bias || "BUY";
    DOM.modalSelectStatus.value = f.status || "WAITING";
    if (DOM.modalInputTrigger) DOM.modalInputTrigger.value = f.trigger || "";
    DOM.modalInputEntry.value = f.entry_zone || "";
    DOM.modalInputSl.value = f.stop_loss || "";
    DOM.modalInputTp1.value = f.tp1 || "";
    DOM.modalInputTp2.value = f.tp2 || "";
    DOM.modalInputRationale.value = f.rationale || "";
    DOM.modalInputNotes.value = f.user_notes || "";

    // Render Checklist Editor
    const checklist = f.checklist || [
        { text: "H4 Demand/Supply Order Block", checked: true },
        { text: "Quét thanh khoản phiên (Sweep Liquidity)", checked: true },
        { text: "Nến xác nhận đảo chiều Price Action", checked: true },
        { text: "EMA xu hướng đồng thuận", checked: true }
    ];

    DOM.modalChecklistEditor.innerHTML = checklist.map((item, idx) => `
        <div class="cl-item-row">
            <input type="checkbox" id="cl_check_${idx}" ${item.checked ? 'checked' : ''}>
            <input type="text" id="cl_text_${idx}" value="${item.text}">
        </div>
    `).join("");

    DOM.editModal.classList.add("active");
}

function closeEditModal() {
    DOM.editModal.classList.remove("active");
}

async function handleTriggerTelegramAlert() {
    if (!STATE.isAdmin) {
        showToast("Vui lòng đăng nhập Admin để phát cảnh báo!", "warning");
        return;
    }
    const p = STATE.activePair;
    const f = STATE.forecasts[p] || {};
    
    try {
        const res = await fetch(`${API_BASE}/api/alerts/telegram`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Admin-Token": STATE.adminToken
            },
            body: JSON.stringify({
                pair: p,
                direction: f.bias || "BUY",
                status: f.status || "ACTIVE",
                entry: f.entry_zone || "",
                sl: String(f.stop_loss || ""),
                tp1: String(f.tp1 || ""),
                tp2: String(f.tp2 || ""),
                trigger: f.trigger || ""
            })
        });
        if (res.ok) {
            showToast(`🚀 Đã phát cảnh báo kịch bản ${p} tới Telegram!`, "success");
        } else {
            showToast("Lỗi khi phát cảnh báo.", "warning");
        }
    } catch (e) {
        showToast("Không thể kết nối máy chủ để phát cảnh báo.", "warning");
    }
}

async function handleSaveScenario(e) {
    e.preventDefault();
    if (!STATE.isAdmin) {
        openLoginModal();
        return;
    }

    const p = DOM.modalInputPair.value;
    const bias = DOM.modalSelectBias.value;
    const status = DOM.modalSelectStatus.value;
    const trigger = DOM.modalInputTrigger ? DOM.modalInputTrigger.value : "";
    const entry = DOM.modalInputEntry.value;
    const sl = parseFloat(DOM.modalInputSl.value) || 0;
    const tp1 = parseFloat(DOM.modalInputTp1.value) || 0;
    const tp2 = parseFloat(DOM.modalInputTp2.value) || 0;
    const rationale = DOM.modalInputRationale.value;
    const userNotes = DOM.modalInputNotes.value;

    // Read checklist items
    const checklistItems = [];
    const rows = DOM.modalChecklistEditor.querySelectorAll(".cl-item-row");
    rows.forEach((row, idx) => {
        const chk = document.getElementById(`cl_check_${idx}`);
        const txt = document.getElementById(`cl_text_${idx}`);
        if (txt && txt.value.trim()) {
            checklistItems.push({
                text: txt.value.trim(),
                checked: chk ? chk.checked : false
            });
        }
    });

    // Calculate approximate R:R
    const entryNum = parseFloat(entry.split("-")[0]) || sl;
    const risk = Math.abs(entryNum - sl);
    const reward = Math.abs(tp2 - entryNum);
    const rrRatio = risk > 0 ? `1:${(reward / risk).toFixed(1)}` : "1:2.5";

    const payload = {
        pair: p,
        bias: bias,
        status: status,
        trigger: trigger,
        entry_zone: entry,
        stop_loss: sl,
        tp1: tp1,
        tp2: tp2,
        rr_ratio: rrRatio,
        rationale: rationale,
        user_notes: userNotes,
        checklist: checklistItems
    };

    try {
        const res = await fetch(`${API_BASE}/api/forecasts/update`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Admin-Token": STATE.adminToken
            },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            STATE.forecasts[p] = data.forecast;
            renderAssetGrid();
            renderActivePairDetail();
            renderMatrixTable();
            closeEditModal();
            showToast(`Đã lưu kịch bản của Mr Tung cho ${p}!`, "success");
        } else if (res.status === 401) {
            showToast("Hết phiên đăng nhập Admin! Vui lòng đăng nhập lại.", "warning");
            openLoginModal();
        } else {
            showToast("Lỗi khi lưu kịch bản.", "warning");
        }
    } catch (err) {
        showToast("Không thể kết nối máy chủ để lưu.", "warning");
    }
}

async function handleResetScenario() {
    if (!STATE.isAdmin) {
        showToast("Vui lòng đăng nhập mật khẩu Admin để khôi phục kịch bản!", "info");
        openLoginModal(handleResetScenario);
        return;
    }

    const p = STATE.activePair;
    if (!confirm(`Mr Tung có muốn khôi phục kịch bản tính toán tự động ban đầu cho ${p}?`)) return;

    try {
        const res = await fetch(`${API_BASE}/api/forecasts/reset/${p}`, {
            method: "POST",
            headers: { "X-Admin-Token": STATE.adminToken }
        });
        if (res.ok) {
            const data = await res.json();
            STATE.forecasts[p] = data.forecast;
            renderAssetGrid();
            renderActivePairDetail();
            renderMatrixTable();
            showToast(`Đã khôi phục kịch bản tự động cho ${p}!`, "info");
        } else if (res.status === 401) {
            showToast("Hết phiên đăng nhập Admin! Vui lòng đăng nhập lại.", "warning");
            openLoginModal(handleResetScenario);
        } else {
            showToast("Lỗi khi khôi phục kịch bản.", "warning");
        }
    } catch (err) {
        showToast("Lỗi khi khôi phục kịch bản.", "warning");
    }
}

async function handleExportText() {
    try {
        const res = await fetch(`${API_BASE}/api/export-text`);
        if (res.ok) {
            const data = await res.json();
            DOM.exportTextArea.value = data.text;
            DOM.exportModal.classList.add("active");
        }
    } catch (err) {
        showToast("Lỗi khi tạo bản xuất kịch bản.", "warning");
    }
}

function handleCopyExport() {
    DOM.exportTextArea.select();
    navigator.clipboard.writeText(DOM.exportTextArea.value);
    DOM.copyBtnText.textContent = "Đã Sao Chép!";
    showToast("Đã sao chép kịch bản tuần vào Clipboard!", "success");
    setTimeout(() => {
        DOM.copyBtnText.textContent = "Sao Chép Toàn Bộ";
    }, 2000);
}

// -------------------------------------------------------------
// Event Listeners Setup
// -------------------------------------------------------------

function setupEventListeners() {
    DOM.btnRefreshAll.addEventListener("click", refreshAllData);
    DOM.btnOpenEditModal.addEventListener("click", openEditModal);
    DOM.btnResetScenario.addEventListener("click", handleResetScenario);
    DOM.btnCloseModal.addEventListener("click", closeEditModal);
    DOM.btnCancelModal.addEventListener("click", closeEditModal);
    DOM.editForm.addEventListener("submit", handleSaveScenario);
    if (DOM.btnTriggerTelegramAlert) DOM.btnTriggerTelegramAlert.addEventListener("click", handleTriggerTelegramAlert);

    // Admin Auth Listeners
    DOM.btnAdminAuth.addEventListener("click", handleAdminButtonClick);
    DOM.loginForm.addEventListener("submit", handleLoginSubmit);
    DOM.btnCloseLogin.addEventListener("click", closeLoginModal);
    DOM.btnCancelLogin.addEventListener("click", closeLoginModal);

    DOM.btnExportText.addEventListener("click", handleExportText);
    DOM.btnCloseExport.addEventListener("click", () => DOM.exportModal.classList.remove("active"));
    DOM.btnCopyExport.addEventListener("click", handleCopyExport);

    // Sidebar Tab Switching
    DOM.tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            DOM.tabButtons.forEach(b => b.classList.remove("active"));
            DOM.tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const targetPane = document.getElementById(tabId);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    // Calendar Filter
    DOM.calendarImpactFilter.addEventListener("change", async () => {
        await loadCalendar();
        renderCalendar();
    });
}

// Start Application
document.addEventListener("DOMContentLoaded", async () => {
    setupEventListeners();
    await initAuth();
    initDashboard();
});

