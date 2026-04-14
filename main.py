"""
MACRO/SIGNAL Dashboard v4.1
============================================================
Install: pip install streamlit pandas plotly fredapi yfinance
Run:     streamlit run macro_dashboard.py
FRED key set in Streamlit Cloud → Manage App → Secrets:
  FRED_API_KEY = "your_key_here"
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from fredapi import Fred
import yfinance as yf
from datetime import datetime, timedelta

# ── API key (Streamlit Secrets only — never exposed to users) ─────────────────
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MACRO/SIGNAL",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Space Grotesk',sans-serif;background:#070d18!important;color:#c9d8eb!important}
.stApp{background:#070d18!important}
.main .block-container{padding:1.2rem 1.6rem 2rem;max-width:1800px}
[data-testid="stSidebar"]{background:#0a1220!important;border-right:1px solid #1a2840}
[data-testid="stMetric"]{background:#0d1b2a;border:1px solid #1a2840;border-radius:8px;padding:.85rem 1rem;position:relative;overflow:hidden}
[data-testid="stMetric"]::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:#22d3ee}
[data-testid="stMetricLabel"]{color:#3a5a7a!important;font-size:.65rem!important;font-family:'IBM Plex Mono',monospace;text-transform:uppercase;letter-spacing:.1em}
[data-testid="stMetricValue"]{color:#e8f4ff!important;font-size:1.4rem!important;font-weight:600;font-family:'IBM Plex Mono',monospace}
[data-testid="stMetricDelta"]{font-family:'IBM Plex Mono',monospace;font-size:.72rem!important}
[data-testid="stTabs"] button{font-family:'IBM Plex Mono',monospace;font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:#3a5a7a}
[data-testid="stTabs"] button[aria-selected="true"]{color:#22d3ee!important}
.stTabs [data-baseweb="tab-border"]{background:#1a2840!important}
.stTabs [data-baseweb="tab-highlight"]{background:#22d3ee!important}
hr{border-color:#1a2840!important}
h1{font-family:'Space Grotesk',sans-serif!important;font-weight:700!important;font-size:1.7rem!important;color:#e8f4ff!important}
h3{font-family:'IBM Plex Mono',monospace!important;font-size:.72rem!important;color:#3a5a7a!important;text-transform:uppercase;letter-spacing:.12em}
[data-testid="stAlert"]{background:#0d1b2a!important;border:1px solid #1a2840!important;border-radius:8px;font-family:'IBM Plex Mono',monospace}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:#0d1b2a}::-webkit-scrollbar-thumb{background:#1a2840;border-radius:3px}
.regime-banner{display:flex;align-items:center;gap:12px;background:#0d1b2a;border:1px solid #1a2840;border-radius:8px;padding:11px 18px;margin-bottom:1rem}
.regime-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.regime-name{font-family:'IBM Plex Mono',monospace;font-size:.82rem;font-weight:600;letter-spacing:.08em}
.regime-desc{font-size:.78rem;color:#7a9bbf;margin-left:auto;text-align:right;max-width:500px}
.live-chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px;border-radius:20px;background:rgba(34,211,238,.07);border:1px solid rgba(34,211,238,.18);font-family:'IBM Plex Mono',monospace;font-size:.65rem;color:#22d3ee}
.live-dot{width:6px;height:6px;border-radius:50%;background:#22d3ee;display:inline-block;animation:blink 1.8s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.sig-pill{display:inline-block;padding:2px 9px;border-radius:4px;font-family:'IBM Plex Mono',monospace;font-size:.68rem;font-weight:600;letter-spacing:.05em}
.sow{background:rgba(34,197,94,.13);color:#4ade80;border:1px solid rgba(34,197,94,.25)}
.ow{background:rgba(134,239,172,.1);color:#86efac;border:1px solid rgba(134,239,172,.2)}
.n{background:rgba(148,163,184,.08);color:#64748b;border:1px solid rgba(148,163,184,.15)}
.uw{background:rgba(252,165,165,.1);color:#fca5a5;border:1px solid rgba(252,165,165,.2)}
.suw{background:rgba(239,68,68,.13);color:#f87171;border:1px solid rgba(239,68,68,.25)}
.hm-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}
.hm-cell{border-radius:6px;padding:9px 7px;text-align:center}
.hm-name{font-size:.72rem;font-weight:500;margin-bottom:3px}
.hm-sig{font-family:'IBM Plex Mono',monospace;font-size:.7rem;font-weight:600}
.scorecard-wrap{background:#0d1b2a;border:1px solid #1a2840;border-radius:8px;padding:12px 14px}
.sc-row{display:grid;grid-template-columns:130px 72px 22px 1fr;gap:5px;align-items:center;padding:5px 0;border-bottom:1px solid rgba(26,40,64,.5)}
.sc-row:last-child{border-bottom:none}
.risk-card{background:#0d1b2a;border:1px solid #1a2840;border-radius:8px;padding:14px}
.risk-title{font-family:'IBM Plex Mono',monospace;font-size:.68rem;color:#3a5a7a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px}
.risk-val{font-family:'IBM Plex Mono',monospace;font-size:1.9rem;font-weight:600;line-height:1}
.risk-label{font-family:'IBM Plex Mono',monospace;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em;margin-top:4px}
.risk-sub{font-size:.7rem;color:#3a5a7a;margin-top:6px}
.spread-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid rgba(26,40,64,.4)}
.spread-row:last-child{border-bottom:none}
.spread-name{font-size:.76rem;color:#7a9bbf}
.spread-val{font-family:'IBM Plex Mono',monospace;font-size:.85rem;font-weight:600}
.pmi-row{margin-bottom:9px}
.pmi-label{display:flex;justify-content:space-between;margin-bottom:3px;font-size:.74rem}
.pmi-track{width:100%;height:7px;background:#111f30;border-radius:4px;position:relative}
.pmi-fill{height:7px;border-radius:4px}
.pmi-mark{position:absolute;top:-2px;width:2px;height:11px;background:rgba(148,163,184,.25);left:50%}
</style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────────────────────────
BG   = "rgba(0,0,0,0)"
GRID = "rgba(26,40,64,0.7)"
MONO = "'IBM Plex Mono', monospace"
TCLR = "#3a5a7a"
C    = dict(blue="#22d3ee", red="#f87171", orange="#fb923c", green="#4ade80",
            purple="#a78bfa", yellow="#f59e0b", teal="#2dd4bf", pink="#f472b6")

def theme(fig, h=340):
    fig.update_layout(
        height=h, paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family=MONO, color=TCLR, size=10),
        legend=dict(bgcolor="rgba(13,27,42,.9)", bordercolor="#1a2840",
                    borderwidth=1, font=dict(size=9)),
        margin=dict(l=8, r=12, t=36, b=28),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=9),
                     showspikes=True, spikecolor="#1a2840", spikethickness=1)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, tickfont=dict(size=9))
    fig.update_annotations(font=dict(size=9, color=TCLR))
    return fig

# ── FRED series IDs ───────────────────────────────────────────────────────────
FRED_IDS = {
    "fed_rate":  "FEDFUNDS",      # Monthly
    "cpi":       "CPIAUCSL",      # Monthly
    "core_cpi":  "CPILFESL",      # Monthly
    "pce":       "PCEPI",         # Monthly
    "unrate":    "UNRATE",        # Monthly
    "gdp":       "GDP",           # Quarterly
    "t10y":      "GS10",          # Monthly
    "t2y":       "GS2",           # Monthly
    "t3m":       "DTB3",          # Daily
    "retail":    "RSAFS",         # Monthly
    "housing":   "HOUST",         # Monthly
    "m2":        "M2SL",          # Monthly
    "vix":       "VIXCLS",        # Daily
    "hy_spread": "BAMLH0A0HYM2",  # Daily — HY credit spread
    "ig_spread": "BAMLC0A0CM",    # Daily — IG credit spread
    "ism_mfg":   "NAPM",          # Monthly — ISM Manufacturing PMI
    "ism_svc":   "NMFCI",         # Monthly — ISM Services PMI
    "sahm":      "SAHMCURRENT",   # Monthly — Sahm Rule indicator
}

# ── Sector ETFs ───────────────────────────────────────────────────────────────
SECTORS = {
    "Healthcare":    "XLV", "Consumer_Stap": "XLP", "Utilities":     "XLU",
    "Financials":    "XLF", "Energy":        "XLE", "Materials":     "XLB",
    "Industrials":   "XLI", "Technology":    "XLK", "Consumer_Disc": "XLY",
    "Real_Estate":   "XLRE","Comm_Services": "XLC",
}
SLABELS = {k: k.replace("_", " ") for k in SECTORS}

# ── Data loaders ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_fred(api_key):
    fred  = Fred(api_key=api_key)
    end   = datetime.today()
    start = end - timedelta(days=365 * 5)
    raw   = {}
    for name, sid in FRED_IDS.items():
        try:
            s = fred.get_series(sid, observation_start=start, observation_end=end)
            if s is not None and len(s) > 0:
                raw[name] = s
        except Exception:
            pass

    frames = {}
    for name, s in raw.items():
        s = s.dropna()
        s.index = pd.to_datetime(s.index)
        if name == "gdp":
            frames[name] = s.resample("QE").last()
        else:
            frames[name] = s.resample("ME").last()

    # Derived series
    if "cpi" in frames:
        frames["cpi_yoy"] = frames["cpi"].pct_change(12) * 100
    if "core_cpi" in frames:
        frames["core_cpi_yoy"] = frames["core_cpi"].pct_change(12) * 100
    if "pce" in frames:
        frames["pce_yoy"] = frames["pce"].pct_change(12) * 100
    if "gdp" in frames:
        frames["gdp_g"] = frames["gdp"].pct_change(4) * 100
    if "m2" in frames:
        frames["m2_g"] = frames["m2"].pct_change(12) * 100
    if "retail" in frames:
        frames["retail_g"] = frames["retail"].pct_change(12) * 100
    if "t10y" in frames and "t2y" in frames:
        tmp = pd.concat([frames["t10y"], frames["t2y"]], axis=1,
                        keys=["t10y", "t2y"]).dropna()
        frames["curve_10_2"] = tmp["t10y"] - tmp["t2y"]
    if "t10y" in frames and "t3m" in frames:
        tmp = pd.concat([frames["t10y"], frames["t3m"]], axis=1,
                        keys=["t10y", "t3m"]).dropna()
        frames["curve_10_3m"] = tmp["t10y"] - tmp["t3m"]

    return pd.DataFrame(frames)

@st.cache_data(ttl=900, show_spinner=False)
def load_etfs():
    rows = []
    for key, ticker in SECTORS.items():
        try:
            hist   = yf.Ticker(ticker).history(period="1y")
            if hist.empty:
                continue
            closes = hist["Close"].dropna()
            now    = float(closes.iloc[-1])
            def pct(n):
                idx  = max(0, len(closes) - n)
                base = float(closes.iloc[idx])
                return round((now / base - 1) * 100, 2) if base > 0 else None
            ys  = closes[closes.index >= f"{datetime.today().year}-01-01"]
            ytd = round((now / float(ys.iloc[0]) - 1) * 100, 2) if len(ys) > 0 else None
            rows.append(dict(key=key, label=SLABELS[key], ticker=ticker,
                             price=round(now, 2), d1=pct(2), m1=pct(22), ytd=ytd))
        except Exception:
            pass
    return rows

# ── Signal engine ─────────────────────────────────────────────────────────────
def latest(df, col):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return round(float(s.iloc[-1]), 4) if len(s) > 0 else None

def prev_val(df, col, n=1):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return round(float(s.iloc[-1 - n]), 4) if len(s) > n else None

def compute(df):
    fed   = latest(df, "fed_rate")     or 0
    cpi   = latest(df, "cpi_yoy")      or 0
    core  = latest(df, "core_cpi_yoy") or 0
    unr   = latest(df, "unrate")       or 0
    gdpg  = latest(df, "gdp_g")        or 0
    cur   = latest(df, "curve_10_2")   or 0
    cur3m = latest(df, "curve_10_3m")  or 0
    m2g   = latest(df, "m2_g")         or 0
    retg  = latest(df, "retail_g")     or 0
    vix   = latest(df, "vix")          or 0
    hy    = latest(df, "hy_spread")    or 0
    ig    = latest(df, "ig_spread")    or 0
    mfg   = latest(df, "ism_mfg")      or 0
    svc   = latest(df, "ism_svc")      or 0
    sahm  = latest(df, "sahm")         or 0

    # Regime classification
    if sahm >= 0.5:
        reg = "SAHM RULE TRIGGERED · RECESSION SIGNAL"
        col = "#f87171"
        desc = f"Sahm indicator at {sahm:.2f} — above 0.5 threshold. Recession likely underway. Maximum defensive positioning."
    elif cpi > 5 and fed > 4:
        reg = "HIGH INFLATION · TIGHT POLICY"
        col = "#f87171"
        desc = "Fed in active tightening. Risk assets under pressure. Energy, Materials and Financials outperform."
    elif cpi > 3 and fed < 3:
        reg = "INFLATION RESURGENCE · POLICY LAG"
        col = "#fb923c"
        desc = "Inflation above target but policy is behind the curve. Watch commodities, TIPS and Materials."
    elif cur < 0 or cur3m < 0:
        reg = "INVERTED YIELD CURVE · RECESSION RISK"
        col = "#f59e0b"
        desc = f"Curve at {cur:.2f}%. Historically precedes recession by 6–18 months. Rotate to defensives."
    elif cpi < 2.5 and fed < 3 and unr < 5 and gdpg > 1.5:
        reg = "GOLDILOCKS · SOFT LANDING"
        col = "#4ade80"
        desc = "Low inflation, easy policy, strong labour. Ideal for broad risk-on. Tech and Consumer Disc lead."
    elif unr > 5.5 or gdpg < 0:
        reg = "RECESSION · RISK-OFF"
        col = "#f87171"
        desc = "Growth contracting. Defensives key. Healthcare, Staples, Utilities, cash preservation."
    else:
        reg = "MID-CYCLE EXPANSION"
        col = "#22d3ee"
        desc = "Normalised expansion. Balanced positioning with tilt toward cyclicals and quality growth."

    # Sector scores
    sc = {k: 0 for k in SECTORS}

    if cpi > 5:
        sc["Energy"] += 2; sc["Materials"] += 2
        sc["Real_Estate"] -= 2; sc["Technology"] -= 1; sc["Utilities"] -= 1
    elif cpi > 3:
        sc["Energy"] += 1; sc["Materials"] += 1; sc["Real_Estate"] -= 1

    if fed > 5:
        sc["Financials"] += 2; sc["Utilities"] -= 2
        sc["Real_Estate"] -= 2; sc["Consumer_Disc"] -= 1
    elif fed > 3:
        sc["Financials"] += 1; sc["Utilities"] -= 1; sc["Real_Estate"] -= 1
    elif fed < 2:
        sc["Real_Estate"] += 1; sc["Utilities"] += 1; sc["Technology"] += 1

    if cur < -0.5 or cur3m < -0.5:
        sc["Healthcare"] += 2; sc["Consumer_Stap"] += 2; sc["Utilities"] += 1
        sc["Industrials"] -= 1; sc["Consumer_Disc"] -= 2; sc["Technology"] -= 1
    elif cur > 1.5:
        sc["Financials"] += 1; sc["Industrials"] += 1

    if gdpg < 0:
        sc["Healthcare"] += 2; sc["Consumer_Stap"] += 2; sc["Utilities"] += 1
        sc["Technology"] -= 2; sc["Consumer_Disc"] -= 2
    elif gdpg > 3:
        sc["Technology"] += 1; sc["Industrials"] += 1; sc["Consumer_Disc"] += 1

    if unr < 4:
        sc["Consumer_Disc"] += 1; sc["Technology"] += 1
    elif unr > 6:
        sc["Consumer_Disc"] -= 2; sc["Real_Estate"] -= 1
        sc["Healthcare"] += 1; sc["Consumer_Stap"] += 1

    if m2g > 8:
        sc["Technology"] += 1; sc["Real_Estate"] += 1
    elif m2g < 0:
        sc["Technology"] -= 1; sc["Real_Estate"] -= 1

    if retg and retg > 5:   sc["Consumer_Disc"] += 1
    elif retg and retg < 0: sc["Consumer_Disc"] -= 1

    if vix > 30:
        sc["Healthcare"] += 1; sc["Consumer_Stap"] += 1
        sc["Technology"] -= 1; sc["Consumer_Disc"] -= 1

    if hy > 6:
        sc["Healthcare"] += 1; sc["Consumer_Stap"] += 1
        sc["Financials"] -= 1; sc["Real_Estate"] -= 1

    if mfg < 50:
        sc["Industrials"] -= 1; sc["Materials"] -= 1
    elif mfg > 55:
        sc["Industrials"] += 1; sc["Materials"] += 1

    if sahm >= 0.5:
        sc["Healthcare"] += 2; sc["Consumer_Stap"] += 2
        sc["Technology"] -= 2; sc["Consumer_Disc"] -= 2

    sc = {k: max(-2, min(2, v)) for k, v in sc.items()}
    conv = min(100, int((abs(cpi - 2.5) + abs(fed - 3) + abs(unr - 4.5) + abs(cur)) * 12))

    return dict(reg=reg, col=col, desc=desc, sc=sc, conv=conv,
                fed=fed, cpi=cpi, core=core, unr=unr, gdpg=gdpg,
                cur=cur, cur3m=cur3m, m2g=m2g, retg=retg,
                vix=vix, hy=hy, ig=ig, mfg=mfg, svc=svc, sahm=sahm)

# ── Display helpers ───────────────────────────────────────────────────────────
PCLS = {2:"sow", 1:"ow", 0:"n", -1:"uw", -2:"suw"}
PTXT = {2:"STRONG OW", 1:"OVERWEIGHT", 0:"NEUTRAL", -1:"UNDERWEIGHT", -2:"STRONG UW"}
BCLR = {2:"#4ade80", 1:"#86efac", 0:"#475569", -1:"#fca5a5", -2:"#f87171"}
HMBG = {2:"rgba(74,222,128,.14)",  1:"rgba(134,239,172,.1)",
        0:"rgba(148,163,184,.07)", -1:"rgba(252,165,165,.1)",
        -2:"rgba(239,68,68,.14)"}
HMCL = {2:"#4ade80", 1:"#86efac", 0:"#64748b", -1:"#fca5a5", -2:"#f87171"}

def pill(score):
    return f'<span class="sig-pill {PCLS[score]}">{PTXT[score]}</span>'

def pct_html(val):
    if val is None:
        return '<span style="color:#3a5a7a">—</span>'
    color = "#4ade80" if val > 0 else "#f87171" if val < 0 else "#64748b"
    sign  = "+" if val > 0 else ""
    return f'<span style="color:{color};font-family:{MONO};font-size:.78rem">{sign}{val:.1f}%</span>'

def trend_arrow(df, col):
    if col not in df.columns:
        return "→", "#64748b"
    s = df[col].dropna()
    if len(s) < 3:
        return "→", "#64748b"
    d = float(s.iloc[-1]) - float(s.iloc[-3])
    if d > 0.05:  return "↑", "#4ade80"
    if d < -0.05: return "↓", "#f87171"
    return "→", "#64748b"

def fmt(val, decimals=2):
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"

def vix_color(v):
    if v is None: return "#64748b"
    if v < 15:   return "#4ade80"
    if v < 20:   return "#86efac"
    if v < 25:   return "#f59e0b"
    if v < 30:   return "#fb923c"
    return "#f87171"

def vix_label(v):
    if v is None: return "N/A"
    if v < 15:   return "Complacent"
    if v < 20:   return "Low Vol"
    if v < 25:   return "Elevated"
    if v < 30:   return "High Stress"
    return "Fear / Crisis"

def spread_color(v, hy=True):
    if v is None: return "#64748b"
    if hy:
        if v < 4:  return "#4ade80"
        if v < 6:  return "#f59e0b"
        return "#f87171"
    else:
        if v < 1:   return "#4ade80"
        if v < 1.5: return "#f59e0b"
        return "#f87171"

def pmi_color(v):
    if v is None: return "#64748b"
    if v >= 55:  return "#4ade80"
    if v >= 50:  return "#86efac"
    if v >= 45:  return "#f59e0b"
    return "#f87171"

def sahm_color(v):
    if v is None: return "#64748b"
    if v < 0.3:  return "#4ade80"
    if v < 0.5:  return "#f59e0b"
    return "#f87171"

def kpi(col, label, val, pval, help_txt="", inv=False):
    with col:
        display = f"{val:.2f}%" if val is not None else "N/A"
        delta   = f"{val - pval:+.2f}" if val is not None and pval is not None else None
        st.metric(label, display, delta,
                  delta_color="inverse" if inv else "normal",
                  help=help_txt)

# ── Sidebar (lookback only — no API key) ─────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙ Settings")
    lb_label = st.selectbox("Chart Lookback", ["1Y", "2Y", "3Y", "5Y"], index=2)
    lb_days  = {"1Y": 365, "2Y": 730, "3Y": 1095, "5Y": 1825}[lb_label]
    st.divider()
    st.caption("Data: FRED · yfinance\nRefreshes hourly. Not financial advice.")

# ── Server-side key guard ─────────────────────────────────────────────────────
if not FRED_API_KEY:
    st.error("Service temporarily unavailable. Please try again later.")
    st.stop()

# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading live data feeds…"):
    df   = load_fred(FRED_API_KEY)
    etfs = load_etfs()

if df.empty:
    st.error("Unable to load market data. Please try again later.")
    st.stop()

sig    = compute(df)
cutoff = datetime.today() - timedelta(days=lb_days)
dfc    = df[df.index >= pd.Timestamp(cutoff)]

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3, 1, 1])
with c1:
    st.markdown("# 📡 MACRO/SIGNAL")
    st.markdown(
        f'<span class="live-chip"><span class="live-dot"></span>'
        f'LIVE &nbsp;·&nbsp; {datetime.now().strftime("%d %b %Y %H:%M")} SGT</span>',
        unsafe_allow_html=True)
with c2:
    st.metric("Signal Conviction", f"{sig['conv']}%",
              help="How many indicators agree on a clear directional signal")
with c3:
    st.metric("Indicators Tracked", "18",
              help="Fed, CPI, Core CPI, PCE, Unemployment, GDP, Yields, Curve, M2, Retail, Housing, VIX, HY/IG Spreads, ISM Mfg/Svc, Sahm Rule")

st.markdown("<br>", unsafe_allow_html=True)

# ── Regime banner ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="regime-banner" style="border-left:3px solid {sig["col"]}">'
    f'<div class="regime-dot" style="background:{sig["col"]}"></div>'
    f'<div class="regime-name" style="color:{sig["col"]}">{sig["reg"]}</div>'
    f'<div class="regime-desc">{sig["desc"]}</div></div>',
    unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
kpi(k1, "Fed Funds Rate",    sig["fed"],  prev_val(df, "fed_rate"),    "FRED: FEDFUNDS")
kpi(k2, "CPI YoY",           sig["cpi"],  prev_val(df, "cpi_yoy"),     "CPI year-over-year % change")
kpi(k3, "Core CPI YoY",      sig["core"], prev_val(df, "core_cpi_yoy"),"CPI excl. food & energy")
kpi(k4, "Unemployment",      sig["unr"],  prev_val(df, "unrate"),      "FRED: UNRATE", inv=True)
kpi(k5, "Yield Curve 10-2Y", sig["cur"],  prev_val(df, "curve_10_2"),  "10Y minus 2Y Treasury yield spread")
kpi(k6, "GDP Growth YoY",    sig["gdpg"], prev_val(df, "gdp_g"),       "Annualised GDP growth (quarterly)")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# RISK INDICATORS ROW: VIX · Credit Spreads · ISM PMI · Sahm Rule
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Risk & Sentiment Indicators")

r1, r2, r3, r4 = st.columns(4)

# ── VIX ───────────────────────────────────────────────────────────────────────
with r1:
    vv   = sig["vix"]
    vc   = vix_color(vv)
    vl   = vix_label(vv)
    vpv  = prev_val(df, "vix")
    vd   = f"{vv - vpv:+.1f} vs prev" if vv and vpv else ""
    vdisp = f"{vv:.1f}" if vv else "N/A"
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">VIX — Volatility Index</div>'
        f'<div class="risk-val" style="color:{vc}">{vdisp}</div>'
        f'<div class="risk-label" style="color:{vc}">{vl}</div>'
        f'<div class="risk-sub">{vd}</div>'
        f'<div class="risk-sub">CBOE · &lt;15 calm · &gt;30 crisis</div>'
        f'</div>', unsafe_allow_html=True)

# ── Credit Spreads ────────────────────────────────────────────────────────────
with r2:
    hyv  = sig["hy"]
    igv  = sig["ig"]
    hyc  = spread_color(hyv, hy=True)
    igc  = spread_color(igv, hy=False)
    hypv = prev_val(df, "hy_spread")
    igpv = prev_val(df, "ig_spread")
    hyd  = f"{hyv - hypv:+.2f}" if hyv and hypv else ""
    igd  = f"{igv - igpv:+.2f}" if igv and igpv else ""
    hydisp = f"{hyv:.2f}%" if hyv else "N/A"
    igdisp = f"{igv:.2f}%" if igv else "N/A"
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Credit Spreads (ICE BofA OAS)</div>'
        f'<div class="spread-row" style="margin-top:4px">'
        f'<span class="spread-name">High Yield</span>'
        f'<span class="spread-val" style="color:{hyc}">{hydisp}'
        f'<span style="font-size:.68rem;color:#3a5a7a;margin-left:5px">{hyd}</span></span>'
        f'</div>'
        f'<div class="spread-row">'
        f'<span class="spread-name">Investment Grade</span>'
        f'<span class="spread-val" style="color:{igc}">{igdisp}'
        f'<span style="font-size:.68rem;color:#3a5a7a;margin-left:5px">{igd}</span></span>'
        f'</div>'
        f'<div class="risk-sub" style="margin-top:8px">HY &gt;6% = stress · IG &gt;1.5% = caution</div>'
        f'</div>', unsafe_allow_html=True)

# ── ISM PMI ───────────────────────────────────────────────────────────────────
with r3:
    mv   = sig["mfg"]
    svv  = sig["svc"]
    mc   = pmi_color(mv)
    sc2  = pmi_color(svv)
    mfill = min(100, mv) if mv else 0
    sfill = min(100, svv) if svv else 0
    mdisp = f"{mv:.1f}" if mv else "N/A"
    sdisp = f"{svv:.1f}" if svv else "N/A"
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">ISM PMI</div>'
        f'<div class="pmi-row">'
        f'<div class="pmi-label">'
        f'<span style="color:#c9d8eb">Manufacturing</span>'
        f'<span style="color:{mc};font-family:{MONO};font-weight:600">{mdisp}</span>'
        f'</div>'
        f'<div class="pmi-track">'
        f'<div class="pmi-fill" style="width:{mfill}%;background:{mc}"></div>'
        f'<div class="pmi-mark"></div></div></div>'
        f'<div class="pmi-row">'
        f'<div class="pmi-label">'
        f'<span style="color:#c9d8eb">Services</span>'
        f'<span style="color:{sc2};font-family:{MONO};font-weight:600">{sdisp}</span>'
        f'</div>'
        f'<div class="pmi-track">'
        f'<div class="pmi-fill" style="width:{sfill}%;background:{sc2}"></div>'
        f'<div class="pmi-mark"></div></div></div>'
        f'<div class="risk-sub">Above 50 = expansion · Below 50 = contraction</div>'
        f'</div>', unsafe_allow_html=True)

# ── Sahm Rule ─────────────────────────────────────────────────────────────────
with r4:
    sv   = sig["sahm"]
    sc3  = sahm_color(sv)
    triggered = sv is not None and sv >= 0.5
    watch     = sv is not None and 0.3 <= sv < 0.5
    slbl = "TRIGGERED ⚠" if triggered else ("WATCH" if watch else "Clear")
    sdisp2 = f"{sv:.2f}" if sv is not None else "N/A"
    sfill2 = min(100, (sv / 1.0) * 100) if sv is not None else 0
    st.markdown(
        f'<div class="risk-card">'
        f'<div class="risk-title">Sahm Rule Recession Indicator</div>'
        f'<div class="risk-val" style="color:{sc3}">{sdisp2}</div>'
        f'<div class="risk-label" style="color:{sc3}">{slbl}</div>'
        f'<div class="risk-sub" style="margin-top:8px">Triggers at 0.50 — 3m avg unemployment rise ≥0.5pp above prior 12m low</div>'
        f'<div style="margin-top:10px;background:#111f30;border-radius:4px;height:7px;overflow:hidden">'
        f'<div style="width:{sfill2}%;height:7px;border-radius:4px;background:{sc3}"></div></div>'
        f'<div style="display:flex;justify-content:space-between;font-family:{MONO};font-size:.62rem;color:#3a5a7a;margin-top:3px">'
        f'<span>0</span><span style="color:#f59e0b">0.5 threshold</span><span>1.0</span></div>'
        f'</div>', unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# SECTOR SIGNALS + ETF TABLE
# ─────────────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1.05], gap="large")

with left:
    st.markdown("### Sector rotation signals")
    sorted_sc  = sorted(sig["sc"].items(), key=lambda x: x[1])
    fig_bar    = go.Figure(go.Bar(
        x=[v for _, v in sorted_sc],
        y=[SLABELS[k] for k, _ in sorted_sc],
        orientation="h",
        marker=dict(color=[BCLR[v] for _, v in sorted_sc],
                    line=dict(color="rgba(255,255,255,.04)", width=1)),
        text=[PTXT[v] for _, v in sorted_sc],
        textposition="outside",
        textfont=dict(family=MONO, size=9, color="#7a9bbf"),
        hovertemplate="<b>%{y}</b><br>Score: %{x}<extra></extra>",
        cliponaxis=False,
    ))
    fig_bar.add_vline(x=0, line_color="rgba(148,163,184,.2)", line_width=1)
    theme(fig_bar, h=380)
    fig_bar.update_layout(
        xaxis=dict(range=[-3.2, 3.2], tickvals=[-2, -1, 0, 1, 2],
                   ticktext=["Strong UW", "UW", "Neutral", "OW", "Strong OW"],
                   gridcolor=GRID, tickfont=dict(size=9)),
        yaxis=dict(tickfont=dict(size=10, family=MONO)),
        margin=dict(l=8, r=105, t=12, b=28),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.markdown("### Live ETF performance")
    if etfs:
        rows_html = ""
        for e in etfs:
            score = sig["sc"].get(e["key"], 0)
            rows_html += (
                f"<tr style='border-bottom:1px solid rgba(26,40,64,.5)'>"
                f"<td style='padding:5px 6px'>"
                f"<span style='color:#c9d8eb;font-size:.78rem'>{e['label']}</span>"
                f"<span style='color:#243a52;font-size:.68rem;margin-left:5px'>{e['ticker']}</span>"
                f"</td>"
                f"<td style='padding:5px 6px;text-align:right;color:#22d3ee;"
                f"font-family:{MONO};font-size:.78rem'>${e['price']}</td>"
                f"<td style='padding:5px 6px;text-align:right'>{pct_html(e['d1'])}</td>"
                f"<td style='padding:5px 6px;text-align:right'>{pct_html(e['m1'])}</td>"
                f"<td style='padding:5px 6px;text-align:right'>{pct_html(e['ytd'])}</td>"
                f"<td style='padding:5px 6px'>{pill(score)}</td>"
                f"</tr>"
            )
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;font-family:{MONO}' role='table'>"
            "<thead><tr style='border-bottom:1px solid #1a2840'>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:left'>SECTOR</th>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:right'>PRICE</th>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:right'>1D</th>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:right'>1M</th>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:right'>YTD</th>"
            "<th style='padding:5px 6px;color:#243a52;font-size:.68rem;text-align:left'>SIGNAL</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True)
    else:
        st.warning("ETF data unavailable.")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# HISTORICAL CHARTS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Historical macro charts")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈  Rates & Inflation",
    "📉  Yield Curve",
    "💼  Labour & Growth",
    "💧  Liquidity",
    "📊  VIX · Spreads · PMI · Sahm",
])

with tab1:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[.55, .45], vertical_spacing=.08,
                        subplot_titles=("Policy rate vs inflation", "PCE & 10Y yield"))
    for col_key, name, color, row, kw in [
        ("fed_rate",     "Fed Rate",  C["blue"],   1, dict(fill="tozeroy", fillcolor="rgba(34,211,238,.05)")),
        ("cpi_yoy",      "CPI YoY",   C["red"],    1, {}),
        ("core_cpi_yoy", "Core CPI",  C["orange"], 1, dict(dash="dot")),
        ("pce_yoy",      "PCE YoY",   C["purple"], 2, {}),
        ("t10y",         "10Y Yield", C["teal"],   2, {}),
    ]:
        if col_key in dfc.columns:
            s  = dfc[col_key].dropna()
            ld = kw.pop("dash", "solid")
            lw = 1.5 if col_key == "core_cpi_yoy" else 2
            fig.add_trace(go.Scatter(x=s.index, y=s.values, name=name,
                line=dict(color=color, width=lw, dash=ld), **kw), row=row, col=1)
    fig.add_hline(y=2, line_dash="dash", line_color="rgba(148,163,184,.25)",
                  annotation_text="2% target", annotation_font_size=9, row=1, col=1)
    theme(fig, h=480)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         row_heights=[.5, .5], vertical_spacing=.08,
                         subplot_titles=("10Y – 2Y spread (inversion monitor)", "10Y – 3M spread"))
    for ck, rn in [("curve_10_2", 1), ("curve_10_3m", 2)]:
        if ck in dfc.columns:
            s = dfc[ck].dropna()
            fig2.add_trace(go.Scatter(x=s.index, y=s.clip(lower=0).values, name="Normal",
                fill="tozeroy", fillcolor="rgba(74,222,128,.1)",
                line=dict(color=C["green"], width=2)), row=rn, col=1)
            fig2.add_trace(go.Scatter(x=s.index, y=s.clip(upper=0).values, name="Inverted",
                fill="tozeroy", fillcolor="rgba(248,113,113,.12)",
                line=dict(color=C["red"], width=2)), row=rn, col=1)
            fig2.add_hline(y=0, line_color="rgba(148,163,184,.3)", line_width=1, row=rn, col=1)
    theme(fig2, h=480)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("⚠ Inversion has preceded every US recession since 1955, typically 6–18 months earlier.")

with tab3:
    fig3 = make_subplots(rows=2, cols=2,
                         subplot_titles=("Unemployment", "GDP growth YoY",
                                         "Retail sales growth YoY", "Housing starts"),
                         vertical_spacing=.12, horizontal_spacing=.08)
    if "unrate" in dfc.columns:
        s = dfc["unrate"].dropna()
        fig3.add_trace(go.Scatter(x=s.index, y=s.values, name="Unemployment",
            line=dict(color=C["purple"], width=2),
            fill="tozeroy", fillcolor="rgba(167,139,250,.07)"), row=1, col=1)
    if "gdp_g" in dfc.columns:
        s = dfc["gdp_g"].dropna()
        fig3.add_trace(go.Bar(x=s.index, y=s.values, name="GDP",
            marker_color=[C["green"] if v >= 0 else C["red"] for v in s.values],
            opacity=.75), row=1, col=2)
        fig3.add_hline(y=0, line_color="rgba(148,163,184,.3)", row=1, col=2)
    if "retail_g" in dfc.columns:
        s = dfc["retail_g"].dropna()
        fig3.add_trace(go.Scatter(x=s.index, y=s.values, name="Retail",
            line=dict(color=C["teal"], width=2)), row=2, col=1)
    if "housing" in dfc.columns:
        s = dfc["housing"].dropna()
        fig3.add_trace(go.Scatter(x=s.index, y=s.values, name="Housing",
            line=dict(color=C["pink"], width=2),
            fill="tozeroy", fillcolor="rgba(244,114,182,.06)"), row=2, col=2)
    theme(fig3, h=480)
    st.plotly_chart(fig3, use_container_width=True)

with tab4:
    fig4 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         row_heights=[.5, .5], vertical_spacing=.08,
                         subplot_titles=("M2 money supply growth YoY", "Fed rate vs 10Y–2Y spread"))
    if "m2_g" in dfc.columns:
        s = dfc["m2_g"].dropna()
        fig4.add_trace(go.Scatter(x=s.index, y=s.values, name="M2 YoY",
            line=dict(color=C["yellow"], width=2),
            fill="tozeroy", fillcolor="rgba(245,158,11,.07)"), row=1, col=1)
        fig4.add_hline(y=0, line_color="rgba(148,163,184,.3)", row=1, col=1)
    if "curve_10_2" in dfc.columns:
        s = dfc["curve_10_2"].dropna()
        fig4.add_trace(go.Scatter(x=s.index, y=s.values, name="10Y–2Y",
            line=dict(color=C["teal"], width=1.5)), row=2, col=1)
    if "fed_rate" in dfc.columns:
        s = dfc["fed_rate"].dropna()
        fig4.add_trace(go.Scatter(x=s.index, y=s.values, name="Fed Rate",
            line=dict(color=C["blue"], width=1.5, dash="dot")), row=2, col=1)
        fig4.add_hline(y=0, line_color="rgba(148,163,184,.3)", row=2, col=1)
    theme(fig4, h=480)
    st.plotly_chart(fig4, use_container_width=True)

with tab5:
    # Row 1: VIX
    fig5 = make_subplots(rows=4, cols=1, shared_xaxes=True,
                         row_heights=[.28, .24, .24, .24],
                         vertical_spacing=.06,
                         subplot_titles=(
                             "VIX — CBOE Volatility Index",
                             "Credit Spreads — HY & IG (ICE BofA OAS, %)",
                             "ISM PMI — Manufacturing vs Services",
                             "Sahm Rule Recession Indicator",
                         ))
    if "vix" in dfc.columns:
        s = dfc["vix"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="VIX",
            line=dict(color=C["orange"], width=2),
            fill="tozeroy", fillcolor="rgba(251,146,60,.07)"), row=1, col=1)
        fig5.add_hline(y=20, line_dash="dash", line_color="rgba(148,163,184,.25)",
                       annotation_text="20 elevated", annotation_font_size=9, row=1, col=1)
        fig5.add_hline(y=30, line_dash="dash", line_color="rgba(248,113,113,.4)",
                       annotation_text="30 crisis", annotation_font_size=9, row=1, col=1)

    if "hy_spread" in dfc.columns:
        s = dfc["hy_spread"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="HY Spread",
            line=dict(color=C["red"], width=2),
            fill="tozeroy", fillcolor="rgba(248,113,113,.07)"), row=2, col=1)
    if "ig_spread" in dfc.columns:
        s = dfc["ig_spread"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="IG Spread",
            line=dict(color=C["teal"], width=1.5, dash="dot")), row=2, col=1)
    if "hy_spread" in dfc.columns:
        fig5.add_hline(y=6, line_dash="dash", line_color="rgba(248,113,113,.35)",
                       annotation_text="6% stress", annotation_font_size=9, row=2, col=1)

    if "ism_mfg" in dfc.columns:
        s = dfc["ism_mfg"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="ISM Mfg",
            line=dict(color=C["blue"], width=2)), row=3, col=1)
    if "ism_svc" in dfc.columns:
        s = dfc["ism_svc"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="ISM Svc",
            line=dict(color=C["purple"], width=1.5, dash="dot")), row=3, col=1)
    fig5.add_hline(y=50, line_dash="dash", line_color="rgba(148,163,184,.3)",
                   annotation_text="50 neutral", annotation_font_size=9, row=3, col=1)

    if "sahm" in dfc.columns:
        s = dfc["sahm"].dropna()
        fig5.add_trace(go.Scatter(x=s.index, y=s.values, name="Sahm Rule",
            line=dict(color=C["yellow"], width=2),
            fill="tozeroy", fillcolor="rgba(245,158,11,.07)"), row=4, col=1)
        fig5.add_hline(y=0.5, line_dash="dash", line_color="#f87171", line_width=1.5,
                       annotation_text="0.5 recession", annotation_font_size=9, row=4, col=1)
        if len(s) > 0:
            fig5.add_hrect(y0=0.5, y1=float(max(s.max() + 0.1, 1.0)),
                           fillcolor="rgba(248,113,113,.06)", line_width=0, row=4, col=1)

    theme(fig5, h=680)
    st.plotly_chart(fig5, use_container_width=True)
    st.caption(
        "VIX >30 = fear/crisis &nbsp;·&nbsp; "
        "HY spread >6% = credit stress &nbsp;·&nbsp; "
        "PMI >50 = expansion &nbsp;·&nbsp; "
        "Sahm ≥0.5 = recession signal"
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# HEATMAP + SCORECARD
# ─────────────────────────────────────────────────────────────────────────────
hm_col, sc_col = st.columns([1.3, 1], gap="large")

with hm_col:
    st.markdown("### Sector regime heatmap")
    cells = "".join(
        f'<div class="hm-cell" style="background:{HMBG[v]};border:1px solid {HMCL[v]}28">'
        f'<div class="hm-name" style="color:{HMCL[v]}">{SLABELS[k]}</div>'
        f'<div class="hm-sig" style="color:{HMCL[v]}">{PTXT[v]}</div></div>'
        for k, v in sig["sc"].items()
    )
    st.markdown(f'<div class="hm-grid">{cells}</div>', unsafe_allow_html=True)

with sc_col:
    st.markdown("### Macro scorecard")
    sc_data = [
        ("Fed Funds",    "fed_rate",      "fed",  "Tight"      if sig["fed"] > 4                          else "Easy"       if sig["fed"] < 2       else "Neutral"),
        ("CPI YoY",      "cpi_yoy",       "cpi",  "Hot"        if sig["cpi"] > 4                          else "Elevated"   if sig["cpi"] > 2.5     else "Anchored"),
        ("Core CPI",     "core_cpi_yoy",  "core", "Sticky"     if sig["core"] > 3                         else "Softening"),
        ("Unemployment", "unrate",        "unr",  "Tight"      if sig["unr"] < 4.5                        else "Loose"),
        ("GDP Growth",   "gdp_g",         "gdpg", "Expanding"  if sig["gdpg"] and sig["gdpg"] > 2         else "Slowing"),
        ("Yield Curve",  "curve_10_2",    "cur",  "Inverted ⚠" if sig["cur"] < 0                          else "Normal"),
        ("VIX",          "vix",           "vix",  vix_label(sig["vix"])),
        ("HY Spread",    "hy_spread",     "hy",   "Stressed ⚠" if sig["hy"] and sig["hy"] > 6             else "Normal"),
        ("IG Spread",    "ig_spread",     "ig",   "Elevated ⚠" if sig["ig"] and sig["ig"] > 1.5           else "Normal"),
        ("ISM Mfg PMI",  "ism_mfg",       "mfg",  "Expanding"  if sig["mfg"] and sig["mfg"] > 50          else "Contracting"),
        ("ISM Svc PMI",  "ism_svc",       "svc",  "Expanding"  if sig["svc"] and sig["svc"] > 50          else "Contracting"),
        ("Sahm Rule",    "sahm",          "sahm", "Triggered ⚠"if sig["sahm"] and sig["sahm"] >= 0.5      else "Watch"      if sig["sahm"] and sig["sahm"] >= 0.3 else "Clear"),
        ("M2 Growth",    "m2_g",          "m2g",  "Contracting ⚠" if sig["m2g"] and sig["m2g"] < 0       else "Expanding"),
        ("Retail Sales", "retail_g",      "retg", "Strong"     if sig["retg"] and sig["retg"] > 4         else "Resilient"),
    ]
    rows = "".join(
        f'<div class="sc-row">'
        f'<span style="color:#7a9bbf;font-family:{MONO};font-size:.7rem">{lbl}</span>'
        f'<span style="color:#22d3ee;font-family:{MONO};font-size:.76rem;font-weight:600;text-align:right">'
        f'{fmt(sig.get(sk))}</span>'
        f'<span style="color:{trend_arrow(df, ck)[1]};font-size:.9rem;text-align:center">'
        f'{trend_arrow(df, ck)[0]}</span>'
        f'<span style="color:#3a5a7a;font-size:.68rem">{rd}</span>'
        f'</div>'
        for lbl, ck, sk, rd in sc_data
    )
    st.markdown(f'<div class="scorecard-wrap">{rows}</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div style="display:flex;justify-content:space-between;padding-top:10px;'
    f'border-top:1px solid #1a2840;margin-top:1rem">'
    f'<span style="font-family:{MONO};font-size:.68rem;color:#1e3552">Data: Federal Reserve FRED · yfinance</span>'
    f'<span style="font-family:{MONO};font-size:.68rem;color:#1e3552">Educational only — not financial advice</span>'
    f'<span style="font-family:{MONO};font-size:.68rem;color:#1e3552">MACRO/SIGNAL v4.1 · {datetime.now().year}</span>'
    f'</div>', unsafe_allow_html=True)
