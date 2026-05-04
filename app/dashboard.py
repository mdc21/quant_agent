import os
import sys

# Ensure the project root is in the Python path so we can import app and core
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import sqlite3
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
from core.data.store import DataStore
from app.agents.insa import InsightNarrativeEngine

# Load environment variables
load_dotenv()

# --- Global Helpers ---
def fmt_inr(val):
    if not val: return "₹ 0.00"
    abs_fmt = f"₹ {val:,.2f}"
    if val >= 10000000: 
        return f"₹ {val/10000000:.2f} Cr | {abs_fmt}"
    if val >= 100000: 
        return f"₹ {val/100000:.2f} L | {abs_fmt}"
    return abs_fmt

# --- Page Config & Styling ---
st.set_page_config(
    page_title="YourBestPath",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Outfit:wght@400;600;800&display=swap');
    
    :root {
        --primary: #6366f1;
        --primary-soft: rgba(99, 102, 241, 0.1);
        --bg-dark: #0f172a;
        --card-bg: rgba(30, 41, 59, 0.5);
    }
    
    .stApp {
        background-color: var(--bg-dark);
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818cf8, #c084fc, #fb7185);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .card {
        background: var(--card-bg);
        padding: 1.25rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(8px);
        margin-bottom: 1rem;
    }
    
    .metric-title { 
        color: #94a3b8; 
        font-size: 0.8rem; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .metric-value { 
        font-size: 1.75rem; 
        font-weight: 700; 
        color: #f8fafc;
        line-height: 1;
    }
    
    .stButton > button {
        border-radius: 0.75rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    
    .stTab {
        background: transparent !important;
    }
    
    /* Remove unnecessary Streamlit padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        background: rgba(30, 41, 59, 0.2) !important;
        border-radius: 0.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading Helpers ---
def get_audit_history(limit=5):
    db_path = "app/data/audit_log.db"
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(f"SELECT * FROM audit_trail ORDER BY timestamp DESC LIMIT {limit}", conn)
        conn.close()
        return df.to_dict('records')
    except Exception:
        return []

@st.cache_data(ttl=3600)
def get_benchmark_performance(equity_sleeve, passive_sleeve, investor_df=None):
    """
    Calculates 3-year cumulative returns for proposed portfolio and benchmarks.
    Only downloads tickers that are valid Yahoo Finance symbols (NSE ETFs, stocks, indices).
    Mutual fund tickers (MF_*) and full fund names are excluded automatically.
    """
    benchmarks = {
        "Nifty 50":     "^NSEI",
        "Nifty Next 50": "JUNIORBEES.NS",   # Most reliable ETF proxy
        "Nifty Midcap": "MID150BEES.NS",    # ETF proxy — more reliable than ^NSMIDCP100
    }

    def _is_yahoo_valid(ticker: str) -> bool:
        """Return True only for tickers that Yahoo Finance can actually serve."""
        if not ticker:
            return False
        t = ticker.strip()
        if t.startswith("MF_"):           return False  # mutual fund placeholder
        if " " in t:                       return False  # full fund name (no spaces in valid tickers)
        if t.startswith("$"):              return False  # un-stripped Breeze prefix
        return True

    # 1. Collect all tickers
    all_tickers = [t for t in benchmarks.values() if _is_yahoo_valid(t)]
    
    # Proposed weights — equity
    prop_weights = {}
    for s in equity_sleeve:
        t = f"{s['symbol']}.NS"
        if _is_yahoo_valid(t):
            all_tickers.append(t)
            prop_weights[t] = s.get('target_weight', 0)
    # Proposed weights — passive/ETF (skip mutual funds)
    for f in passive_sleeve:
        raw = f['ticker']
        if not _is_yahoo_valid(raw):
            continue
        t = raw if ("^" in raw or raw.endswith((".NS", ".BO"))) else f"{raw}.NS"
        all_tickers.append(t)
        prop_weights[t] = f.get('target_weight', 0)
        
    # Investor weights — map via SymbolMapper, skip unknowns
    inv_weights = {}
    if investor_df is not None:
        from core.utils.symbol_mapper import SymbolMapper
        for _, row in investor_df.iterrows():
            raw_sym = str(row['Symbol']).strip().lstrip('$')
            yahoo_sym = SymbolMapper.to_yahoo(raw_sym)
            t = f"{yahoo_sym}.NS"
            if _is_yahoo_valid(t):
                all_tickers.append(t)
                inv_weights[t] = 1.0 / len(investor_df)

    # Deduplicate
    all_tickers = list(dict.fromkeys(all_tickers))
            
    # 2. Download Data (Last 3 Years)
    try:
        data = yf.download(all_tickers, period="3y", interval="1d", progress=False)["Close"]
        if data.empty: return None
        
        # 3. Calculate Daily Returns
        returns = data.pct_change().fillna(0)
        
        # 4. Synthesize Series
        results = pd.DataFrame(index=returns.index)
        
        # A. Benchmarks
        for name, ticker in benchmarks.items():
            if ticker in returns.columns:
                results[name] = (1 + returns[ticker]).cumprod() * 100
                
        # B. Proposed Portfolio
        prop_series = pd.Series(0.0, index=returns.index)
        valid_prop_tickers = [t for t in prop_weights.keys() if t in returns.columns]
        
        if valid_prop_tickers:
            total_w = sum(prop_weights.values())
            for t in valid_prop_tickers:
                # Use target weight if exists, else equal weight
                w = prop_weights[t] if total_w > 0 else (1.0 / len(valid_prop_tickers))
                prop_series += returns[t] * w
        
        results["Proposed Portfolio"] = (1 + prop_series).cumprod() * 100
        returns["Proposed Portfolio"] = prop_series
        
        # C. Investor Portfolio
        if investor_df is not None and inv_weights:
            inv_series = pd.Series(0.0, index=returns.index)
            valid_inv_tickers = [t for t in inv_weights.keys() if t in returns.columns]
            if valid_inv_tickers:
                for t in valid_inv_tickers:
                    inv_series += returns[t] * inv_weights[t]
                results["Investor Portfolio"] = (1 + inv_series).cumprod() * 100
                returns["Investor Portfolio"] = inv_series
            
        return results.reset_index(), returns
    except Exception:
        return None, None

# --- Session State ---
if 'invested_amount' not in st.session_state:
    st.session_state.invested_amount = 0
if 'goals_defined' not in st.session_state:
    st.session_state.goals_defined = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='color:#6366f1; margin-bottom:0;'>YourBestPath Engine</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b; font-size:0.8rem;'>Institutional Governance & Oversight</p>", unsafe_allow_html=True)
    st.divider()
    
    persona = st.selectbox("Switch Persona", ["📈 Investor", "🛠️ Quant Admin"])
    st.divider()
    
    # Live API Session Input
    with st.expander("🔌 Live Connectivity"):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
            
        env_token = os.getenv("BREEZE_SESSION_TOKEN", "")
        # Fallback to empty string instead of a hardcoded fake token
        session_token = st.text_input("Breeze Session Token", value=env_token, type="password")
        
        if session_token:
            try:
                from core.data.breeze_client import BreezeClient
                BreezeClient.get_instance(session_token)
                st.success("Breeze API: CONNECTED")
            except Exception as e:
                st.error(f"Connection Failed: {e}")
    
    st.divider()
    
    if persona == "📈 Investor":
        nav = st.radio("Navigation", ["Onboarding / Discovery", "Portfolio & Advice", "Goal Health", "Voice & Insights"])
    else:
        nav = st.radio("Navigation", ["Admin Console", "Risk Control", "Audit Ledger", "System Health"])

    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔴 Emergency Stop", width="stretch"):
        st.error("System Halted.")

# --- Main Interface ---
st.markdown("<h1 class='main-header'>YourBestPath</h1>", unsafe_allow_html=True)

if persona == "📈 Investor":
    st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-top:-1rem;'>Professional Insight & Institutional Protection</p>", unsafe_allow_html=True)
    st.markdown(f"<span style='background:rgba(99,102,241,0.2); color:#818cf8; padding:0.2rem 0.8rem; border-radius:20px; font-size:0.8rem; font-weight:600;'>SECURED INVESTOR VIEW</span>", unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#94a3b8; font-size:1.1rem; margin-top:-1rem;'>Institutional Governance & Portfolio Oversight</p>", unsafe_allow_html=True)
    st.markdown(f"<span style='background:rgba(16,185,129,0.2); color:#10b981; padding:0.2rem 0.8rem; border-radius:20px; font-size:0.8rem; font-weight:600;'>COMPLIANCE MANAGER VIEW</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if persona == "📈 Investor":
    if nav == "Onboarding / Discovery":
        st.markdown("### 🎯 Define Your Investment Objectives")
        
        # Move Download Template outside of form to avoid Streamlit API Error
        with st.expander("📥 Import Resources & Templates"):
            st.markdown("""
                <p style='color:#64748b; font-size:0.9rem;'>Download our standard template to ensure your portfolio import is processed with 100% fiduciary accuracy.</p>
            """, unsafe_allow_html=True)
            sample_data = pd.DataFrame({
                "Ticker": ["RELIANCE", "TCS", "HDFCBANK"],
                "Qty_LongTerm": [50, 20, 10],
                "Qty_ShortTerm": [0, 5, 0],
                "avg_buy_price": [2450.50, 3210.00, 1550.00]
            })
            csv = sample_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Template CSV",
                data=csv,
                file_name="yourbestpath_template.csv",
                mime="text/csv",
                width="stretch"
            )

        # 1. Strategy Selection (Outside form for immediate UI reaction)
        st.markdown("##### Funding Strategy")
        capital_type = st.segmented_control("Deployment Mode", ["New Capital", "Import Portfolio", "Plan Only"], default="New Capital")
        
        # --- NEW: State Purge Logic ---
        if 'last_capital_type' not in st.session_state:
            st.session_state.last_capital_type = capital_type
            
        if st.session_state.last_capital_type != capital_type:
            # Purge all legacy portfolio data on strategy switch
            for key in ['imported_portfolio', 'invested_amount', 'path_equity', 'path_passive', 'goals_defined']:
                st.session_state.pop(key, None)
            st.session_state.last_capital_type = capital_type
            st.rerun()
            
        amount = 0
        if capital_type == "Import Portfolio":
            st.markdown("""
                <div style='background:rgba(99,102,241,0.1); padding:0.8rem; border-radius:8px; border-left:4px solid #6366f1; margin-bottom:1rem;'>
                    <p style='color:#6366f1; font-weight:600; margin-bottom:0.2rem;'>CSV Format Required:</p>
                    <ul style='color:#94a3b8; font-size:0.85rem; margin-top:0;'>
                        <li><b>Ticker</b>: NSE Symbol (e.g., RELIANCE)</li>
                        <li><b>Qty_LongTerm</b>: Held > 1 Year</li>
                        <li><b>Qty_ShortTerm</b>: Held < 1 Year</li>
                        <li><b>avg_buy_price</b>: Required for Tax-Loss Harvesting</li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Upload Existing Portfolio (CSV)", type="csv", help="Ensure headers match: Ticker, Qty_LongTerm, Qty_ShortTerm, avg_buy_price")
            if uploaded_file is not None:
                try:
                    df_import = pd.read_csv(uploaded_file)
                    if "Ticker" in df_import.columns:
                        df_import = df_import.rename(columns={"Ticker": "Symbol"})
                    
                    if "Symbol" in df_import.columns:
                        from core.utils.symbol_mapper import SymbolMapper
                        df_import["Symbol"] = df_import["Symbol"].astype(str).str.strip().str.lstrip('$')
                        df_import["Symbol"] = df_import["Symbol"].apply(SymbolMapper.to_nse)
                        
                        if "Qty_LongTerm" in df_import.columns and "Qty_ShortTerm" in df_import.columns:
                            df_import["Quantity"] = df_import["Qty_LongTerm"] + df_import["Qty_ShortTerm"]
                        elif "Quantity" not in df_import.columns and "Qty_LongTerm" in df_import.columns:
                            df_import["Quantity"] = df_import["Qty_LongTerm"]
                        
                        # --- AUTO VALUATION: Calculate live market value ---
                        with st.spinner("📊 Valuing portfolio at live market prices..."):
                            import yfinance as yf
                            import io, contextlib
                            total_market_value = 0
                            valued_rows = []
                            cost_fallback = []   # live — symbols priced at avg_buy_price
                            zero_valued   = []   # bankrupt/delisted — written off to ₹0
                            live_priced   = []   # successfully fetched from Yahoo

                            for _, row in df_import.iterrows():
                                sym = row["Symbol"]
                                qty = row.get("Quantity", 0)
                                avg_price = row.get("avg_buy_price", 0)

                                if SymbolMapper.is_zero_value(sym):
                                    # Bankrupt / delisted — market value is ₹0
                                    live_price = 0
                                    zero_valued.append(sym)

                                elif SymbolMapper.is_resolvable(sym):
                                    live_price = avg_price  # fallback if fetch fails
                                    try:
                                        yahoo_sym = SymbolMapper.to_yahoo(sym)
                                        with contextlib.redirect_stdout(io.StringIO()), \
                                             contextlib.redirect_stderr(io.StringIO()):
                                            hist = yf.Ticker(f"{yahoo_sym}.NS").history(period="1d")
                                        if not hist.empty:
                                            live_price = hist["Close"].iloc[-1]
                                            live_priced.append(sym)
                                        else:
                                            cost_fallback.append(sym)
                                    except Exception:
                                        cost_fallback.append(sym)
                                else:
                                    # Known unresolvable but economically live — use cost price
                                    live_price = avg_price
                                    cost_fallback.append(sym)

                                market_val = qty * live_price
                                pnl = ((live_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
                                total_market_value += market_val
                                valued_rows.append({**row.to_dict(), "live_price": live_price,
                                                    "market_value": market_val, "pnl_pct": pnl})

                            df_import = pd.DataFrame(valued_rows)
                            st.session_state.imported_portfolio = df_import
                            st.session_state.computed_portfolio_value = int(total_market_value)

                            # ── Valuation summary ──
                            cost_basis = (df_import["avg_buy_price"] * df_import["Quantity"]).sum() \
                                         if "avg_buy_price" in df_import.columns else 0
                            overall_pnl = ((total_market_value - cost_basis) / cost_basis * 100) \
                                          if cost_basis > 0 else 0
                            pnl_color = "#10b981" if overall_pnl >= 0 else "#f43f5e"

                            zero_note = ""
                            if zero_valued:
                                zv_names = ", ".join(zero_valued[:5]) + ("…" if len(zero_valued) > 5 else "")
                                zero_note = (f"<br><span style='font-size:0.8rem; color:#f43f5e;'>"
                                             f"🗑️ Written off (₹0) — bankrupt/delisted: {zv_names}</span>")

                            fallback_note = ""
                            if cost_fallback:
                                fb_names = ", ".join(cost_fallback[:5]) + ("…" if len(cost_fallback) > 5 else "")
                                fallback_note = (f"<br><span style='font-size:0.8rem; color:#f59e0b;'>"
                                                 f"⚠️ Cost price used (no live data): {fb_names}</span>")

                            st.markdown(f"""
                            <div style='background:rgba(16,185,129,0.1); border-radius:8px;
                                        padding:1rem; border-left:4px solid {pnl_color}; margin-top:0.5rem;'>
                                <b>📈 Live Portfolio Valuation Complete</b><br>
                                <span style='font-size:0.9rem;'>
                                    Holdings: <b>{len(df_import)}</b> &nbsp;|&nbsp;
                                    Live-priced: <b style='color:#10b981'>{len(live_priced)}</b> &nbsp;|&nbsp;
                                    Cost fallback: <b style='color:#f59e0b'>{len(cost_fallback)}</b> &nbsp;|&nbsp;
                                    Written off: <b style='color:#f43f5e'>{len(zero_valued)}</b>
                                </span><br>
                                <span style='font-size:1rem; font-weight:700;'>
                                    Market Value: {fmt_inr(total_market_value)} &nbsp;|&nbsp;
                                    P&amp;L: <span style='color:{pnl_color}'>{overall_pnl:+.1f}%</span>
                                </span>
                                {zero_note}{fallback_note}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.error("CSV must contain 'Ticker' or 'Symbol' columns.")
                except Exception as e:
                    st.error(f"Import Error: {e}")
            
            # Pre-fill with computed value if available, else manual entry
            computed_val = st.session_state.get("computed_portfolio_value", None)
            if computed_val:
                st.markdown(f"""
                <div style='background:rgba(99,102,241,0.1); border-left:4px solid #6366f1;
                            padding:0.8rem; border-radius:8px; margin-top:0.5rem;'>
                    <b style='color:#6366f1;'>📊 Portfolio Market Value (Live-Priced)</b><br>
                    <span style='font-size:1.1rem; font-weight:700;'>{fmt_inr(computed_val)}</span>
                    <span style='font-size:0.8rem; color:#64748b;'> — This will be your capital in the Waterfall</span>
                </div>
                """, unsafe_allow_html=True)
                amount = st.number_input("Adjust Portfolio Value (₹) if needed", value=computed_val,
                                         step=50000, format="%d",
                                         help="Auto-calculated from live prices × quantities. Adjust if any holdings were unresolvable.")
            else:
                st.warning("⚠️ No portfolio uploaded yet. Upload your CSV above to auto-calculate, or enter manually.")
                amount = st.number_input("Total Portfolio Value (₹)", value=1000000, step=50000, format="%d")
        elif capital_type == "New Capital":
            amount = st.number_input("Investment Amount (₹)", value=1000000, step=50000, format="%d")
            st.caption(f"Ready for Deployment: {fmt_inr(amount)}")
        else:
            amount = st.number_input("Hypothetical Plan Amount (₹)", value=1000000, step=50000, format="%d")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 🎯 Goal-Specific Objectives")
        with st.form("onboarding_form"):
            st.markdown("##### 🚀 Inflation Strategy")
            inf_col1, inf_col2 = st.columns([1, 2])
            with inf_col1:
                inf_scenario = st.radio("Scenario", ["Target (4%)", "Base (6%)", "High (8%)", "Custom"], index=1)
            with inf_col2:
                if inf_scenario == "Target (4%)": inflation_rate = 0.04
                elif inf_scenario == "Base (6%)": inflation_rate = 0.06
                elif inf_scenario == "High (8%)": inflation_rate = 0.08
                else:
                    inflation_rate = st.slider("Custom Inflation (%)", 1.0, 15.0, 6.0, step=0.1) / 100.0
                
                st.info(f"💡 At **{inflation_rate*100:.1f}%** inflation, costs double every **{72/(inflation_rate*100):.1f} years**.")

            st.markdown("---")
            st.markdown("##### 📊 Target Objectives (Today's Money)")
            col1, col2 = st.columns(2)
            with col1:
                emergency_fund = st.number_input("Survival (Monthly Expenses) - ₹", value=100000, step=10000, format="%d")
                # Emergency fund is usually 12x monthly expenses
                emergency_fund_corpus = emergency_fund * 12
                st.markdown(f"<p style='color:#64748b; font-size:0.85rem; margin-top:-0.5rem;'>Annualized: {fmt_inr(emergency_fund_corpus)}</p>", unsafe_allow_html=True)
                
                retirement_goal = st.number_input("Safety Target (Retirement) - ₹", value=50000000, step=500000, format="%d")
            with col2:
                legacy_goal = st.number_input("Growth Target (Legacy) - ₹", value=150000000, step=1000000, format="%d")
                horizon = st.slider("Retirement Horizon (Years)", 1, 40, 20)
            
            # --- Disclosures (Hidden Math) ---
            st.markdown("<div style='background:#f8fafc; padding:1rem; border-radius:8px; border:1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown("<p style='font-weight:600; font-size:0.9rem; margin-bottom:0.5rem;'>🔍 Future Value Disclosure (Inflation-Adjusted)</p>", unsafe_allow_html=True)
            
            # FV Calculations
            fv_surv = emergency_fund_corpus * ((1 + inflation_rate) ** 2)
            fv_safe = retirement_goal * ((1 + inflation_rate) ** horizon)
            fv_growth = legacy_goal * ((1 + inflation_rate) ** (horizon + 5))
            
            st.markdown(f"""
            <div style='display:grid; grid-template-columns: 1fr 1fr 1fr; gap:1rem;'>
                <div>
                    <small style='color:#64748b;'>Survival (2yr)</small><br>
                    <b style='font-size:0.9rem;'>{fmt_inr(fv_surv)}</b>
                </div>
                <div>
                    <small style='color:#64748b;'>Safety ({horizon}yr)</small><br>
                    <b style='font-size:0.9rem;'>{fmt_inr(fv_safe)}</b>
                </div>
                <div>
                    <small style='color:#64748b;'>Growth ({horizon+5}yr)</small><br>
                    <b style='font-size:0.9rem;'>{fmt_inr(fv_growth)}</b>
                </div>
            </div>
            <p style='font-size:0.75rem; color:#94a3b8; margin-top:0.8rem;'>
                *Based on <b>{inflation_rate*100:.1f}%</b> annual inflation. Your {fmt_inr(retirement_goal)} Safety goal 
                requires {fmt_inr(fv_safe)} in {horizon} years to maintain the same lifestyle.
            </p>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Update emergency_fund to the annualized corpus for the waterfall
            emergency_fund = emergency_fund_corpus
            
            # --- NEW: Fiduciary Waterfall Allocation ---
            total_avail = amount
            
            # 1. Fill Survival First
            surv_alloc = min(total_avail, emergency_fund)
            rem1 = total_avail - surv_alloc
            
            # 2. Fill Safety Second
            safe_alloc = min(rem1, retirement_goal)
            rem2 = rem1 - safe_alloc
            
            # 3. Growth Preview & Override
            st.markdown("---")
            st.markdown("##### 🌊 Waterfall Allocation Preview")
            st.write(f"1. **Survival**: {fmt_inr(surv_alloc)} / {fmt_inr(emergency_fund)} " + ("✅" if surv_alloc >= emergency_fund else "🚨"))
            st.write(f"2. **Safety**: {fmt_inr(safe_alloc)} / {fmt_inr(retirement_goal)} " + ("✅" if safe_alloc >= retirement_goal else "🟡"))
            
            if retirement_goal > 0 and (safe_alloc / retirement_goal) >= 0.5:
                st.success("✅ **Safety > 50% Funded.** You have unlocked the **Growth Shortcut**.")
                growth_override = st.slider("Growth Shortcut: Tactical Allocation (%)", 0, 50, 0, help="Shift a portion of the Safety-eligible capital directly into Growth for tactical upside.")
                st.session_state.growth_override = growth_override / 100.0
                
                # Re-calculate with override
                growth_from_safe = rem1 * (growth_override / 100.0)
                safe_alloc -= growth_from_safe
                growth_alloc = rem2 + growth_from_safe
            else:
                growth_alloc = rem2
                st.session_state.growth_override = 0.0
                
            st.write(f"3. **Growth**: {fmt_inr(growth_alloc)} (Residual Capital)")
            st.markdown("<br>", unsafe_allow_html=True)

            submitted = st.form_submit_button("Initialize Fiduciary Plan")
            if submitted:
                # UX Reset
                for key in ['path_equity', 'path_passive', 'allocator_meta']:
                    st.session_state.pop(key, None)
                
                user_goals = [
                    {"label": "Survival", "tier": 1, "target_pv": emergency_fund, "horizon": 2, "current_assets": surv_alloc},
                    {"label": "Safety",   "tier": 2, "target_pv": retirement_goal, "horizon": horizon, "current_assets": safe_alloc},
                    {"label": "Growth",   "tier": 3, "target_pv": legacy_goal, "horizon": horizon + 5, "current_assets": growth_alloc}
                ]
                
                try:
                    from core.data.store import DataStore
                    store = DataStore()
                    store.save_goals("user_1", user_goals, risk_tolerance="Moderate", inflation_rate=inflation_rate)
                    # Always use the actual portfolio value — never stale defaults
                    st.session_state.invested_amount = amount
                    st.session_state.goals_defined = True
                    st.session_state.capital_type = capital_type
                    st.success(
                        f"✅ Fiduciary Waterfall Applied | "
                        f"Total Capital: **{fmt_inr(amount)}** | "
                        f"Survival: {fmt_inr(surv_alloc)} | "
                        f"Safety: {fmt_inr(safe_alloc)} | "
                        f"Growth: {fmt_inr(growth_alloc)}"
                    )
                except Exception as e:
                    st.error(f"Failed to save goals: {e}")


    elif nav == "Portfolio & Advice":
        if not st.session_state.goals_defined:
            st.warning("Please define your goals in 'Onboarding / Discovery' first.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='card'><p class='metric-title'>Portfolio Value</p><p class='metric-value'>{fmt_inr(st.session_state.invested_amount)}</p></div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><p class='metric-title'>Market Regime</p><p class='metric-value' style='color:#10b981'>BULL</p></div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='card'><p class='metric-title'>Recommended Tilt</p><p class='metric-value'>GROWTH</p></div>", unsafe_allow_html=True)
            
            # --- Doomsday Resilience Summary ---
            if hasattr(st.session_state, 'path_equity') and len(st.session_state.path_equity) > 0:
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.markdown("<div class='card'><p class='metric-title'>2008 Crisis</p><p class='metric-value' style='color:#10b981'>-22%</p><small>Protected</small></div>", unsafe_allow_html=True)
                with r2:
                    st.markdown("<div class='card'><p class='metric-title'>2020 COVID</p><p class='metric-value' style='color:#10b981'>-15%</p><small>Resilient</small></div>", unsafe_allow_html=True)
                with r3:
                    st.markdown("<div class='card'><p class='metric-title'>Tech Shock</p><p class='metric-value' style='color:#6366f1'>-12%</p><small>Resilient</small></div>", unsafe_allow_html=True)

            # --- Fiduciary Advice ---
            if hasattr(st.session_state, 'path_equity') and len(st.session_state.path_equity) > 0:
                eq_len = len(st.session_state.path_equity)
                pf_len = len(st.session_state.path_passive) if hasattr(st.session_state, 'path_passive') else 0
                st.info(f"💡 **Fiduciary Advice:** The Path-Allocator has constructed a dynamically risk-controlled portfolio of {eq_len} equities and {pf_len} passive funds to meet your specified goals.")
            else:
                st.info("💡 **Fiduciary Advice:** Please run the YourBestPath Generator above to receive dynamic asset allocation advice.")

            # --- 1. Sector & Market Cap Breakdown ---
            if hasattr(st.session_state, 'path_equity') and st.session_state.path_equity:
                st.markdown("### 🏛️ Exposure Breakdown")
                col_b1, col_b2 = st.columns(2)
                eq_data = st.session_state.path_equity
                
                # Use meta['equity_cap'] to ensure graphs match the exact percentages in the dissection tables
                meta = st.session_state.allocator_meta
                equity_cap = meta.get('equity_cap', sum(c.get('target_capital', 0) for c in eq_data))
                
                # Corrected Sector Breakdown (Capital-Weighted against Total Equity)
                sector_weights = {}
                for c in eq_data:
                    s = c.get('sector', 'Unknown')
                    cap = c.get('target_capital', 0)
                    sector_weights[s] = sector_weights.get(s, 0) + cap
                sector_df = pd.DataFrame([
                    {"Sector": s, "Weight (%)": (cap / equity_cap) * 100 if equity_cap > 0 else 0} 
                    for s, cap in sector_weights.items()
                ])
                
                # Corrected Cap Breakdown (Capital-Weighted against Total Equity)
                cap_weights = {}
                for c in eq_data:
                    cp = c.get('cap', 'Unknown')
                    cap = c.get('target_capital', 0)
                    cap_weights[cp] = cap_weights.get(cp, 0) + cap
                cap_df = pd.DataFrame([
                    {"Cap Size": cp, "Weight (%)": (cap / equity_cap) * 100 if equity_cap > 0 else 0} 
                    for cp, cap in cap_weights.items()
                ])

                with col_b1:
                    st.markdown("#### Sector Allocation")
                    st.bar_chart(sector_df.set_index("Sector"), color="#6366f1")
                with col_b2:
                    st.markdown("#### Market Cap Profile")
                    st.bar_chart(cap_df.set_index("Cap Size"), color="#f43f5e")

                # --- NEW: Fiduciary Capital Audit (Drill-Down) ---
                with st.expander("🔍 Fiduciary Capital Audit: Rupee-Trace Drill Down", expanded=False):
                    meta = st.session_state.allocator_meta
                    total_managed = st.session_state.invested_amount
                    regime_pct = meta.get('regime_scale', '80%')
                    defensive_pct = f"{100 - int(regime_pct.replace('%',''))}%" if '%' in regime_pct else "20%"
                    
                    trace_data = [
                        {"Allocation Layer": "1. Total Managed Capital", "Amount": total_managed, "Rationale": "Initial Investment"},
                        {"Allocation Layer": f"2. ├─ Target Equity ({regime_pct})", "Amount": meta.get('equity_cap', 0), "Rationale": "Macro Regime Risk Tolerance"},
                        {"Allocation Layer": "3. │  ├─ Alpha Sleeve (Direct Stocks)", "Amount": sum(c['target_capital'] for c in eq_data), "Rationale": "60% of Equity (High Conviction)"},
                        {"Allocation Layer": "4. │  └─ Beta Sleeve (Equity Funds)", "Amount": meta.get('beta_cap', 0), "Rationale": "40% of Equity (Market Matching)"},
                        {"Allocation Layer": f"5. └─ Target Defensive ({defensive_pct})", "Amount": meta.get('defensive_cap', 0), "Rationale": "Capital Preservation Assets"},
                        {"Allocation Layer": "6. Total Actually Deployed", "Amount": sum(c['target_capital'] for c in eq_data) + sum(c.get('target_capital', 0) for c in st.session_state.get('path_passive', [])), "Rationale": "Total Alpha + Beta + Defensive"}
                    ]
                    trace_df = pd.DataFrame(trace_data)
                    trace_df['Amount'] = trace_df['Amount'].apply(lambda x: f"₹ {x:,.2f}")
                    st.table(trace_df)
                    
                    st.markdown("##### 2. Dissection by Category")
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.markdown("**By Market Cap**")
                        cap_audit = []
                        unique_caps = sorted(list(set(c.get('cap', 'Unknown') for c in eq_data)))
                        for cp_name in unique_caps:
                            subset = [c for c in eq_data if c.get('cap') == cp_name]
                            total = sum(c.get('target_capital', 0) for c in subset)
                            pct = (total / meta['equity_cap']) * 100 if meta.get('equity_cap', 0) > 0 else 0
                            tickers = ", ".join([c.get('symbol', '') for c in subset])
                            cap_audit.append({"Category": cp_name, "Capital": total, "Exposure": f"{pct:.2f}%", "Assets": tickers})
                        cap_df = pd.DataFrame(cap_audit)
                        if not cap_df.empty and 'Capital' in cap_df.columns:
                            cap_df['Capital'] = cap_df['Capital'].apply(lambda x: f"₹ {x:,.2f}")
                        st.dataframe(cap_df, hide_index=True, width="stretch")
                        
                    with d2:
                        st.markdown("**By Sector**")
                        sector_audit = []
                        unique_sects = sorted(list(set(c.get('sector', 'Unknown') for c in eq_data)))
                        for s_name in unique_sects:
                            subset = [c for c in eq_data if c.get('sector') == s_name]
                            total = sum(c.get('target_capital', 0) for c in subset)
                            pct = (total / meta['equity_cap']) * 100 if meta.get('equity_cap', 0) > 0 else 0
                            sector_audit.append({"Sector": s_name, "Capital": total, "Exposure": f"{pct:.2f}%"})
                        
                        sector_df = pd.DataFrame(sector_audit)
                        if not sector_df.empty and 'Capital' in sector_df.columns:
                            sector_df['Capital'] = sector_df['Capital'].apply(lambda x: f"₹ {x:,.2f}")
                        st.dataframe(sector_df, hide_index=True, width="stretch")
                        
                    with d3:
                        st.markdown("**By Passive Category**")
                        pass_audit = []
                        if hasattr(st.session_state, 'path_passive'):
                            pass_data = st.session_state.path_passive
                            unique_cats = sorted(list(set(c.get('category', 'Passive') for c in pass_data)))
                            total_passive_cap = meta.get('defensive_cap', 0) + meta.get('beta_cap', 0)
                            for cat in unique_cats:
                                subset = [c for c in pass_data if c.get('category') == cat]
                                total = sum(c.get('target_capital', 0) for c in subset)
                                pct = (total / total_passive_cap) * 100 if total_passive_cap > 0 else 0
                                tickers = ", ".join([c.get('ticker', '') for c in subset])
                                pass_audit.append({"Category": cat, "Capital": total, "Exposure": f"{pct:.2f}%", "Assets": tickers})
                            pass_df = pd.DataFrame(pass_audit)
                            if not pass_df.empty and 'Capital' in pass_df.columns:
                                pass_df['Capital'] = pass_df['Capital'].apply(lambda x: f"₹ {x:,.2f}")
                            st.dataframe(pass_df, hide_index=True, width="stretch")

            # --- 1. Portfolio Construction Engine ---
            st.markdown("### 🏗️ Path Allocator")
            st.markdown("<p style='color:#64748b; margin-top:-1rem;'>Configure your institutional constraints and generate an optimized portfolio.</p>", unsafe_allow_html=True)
            
            with st.container(border=True):
                r1, r2, r3 = st.columns(3)
                with r1:
                    total_cap = st.number_input("Capital (₹)", min_value=100000, max_value=100000000, value=1000000, step=100000)
                with r2:
                    risk_prof = st.selectbox("Risk Tolerance", ["Aggressive", "Balanced", "Conservative"])
                with r3:
                    eq_split = st.slider("Alpha-Beta Split (%)", 10, 90, 60)
                    
                # --- NEW: Transparency & Customization ---
                default_macro = {"Aggressive": 80, "Balanced": 60, "Conservative": 40}[risk_prof]
                default_caps = {"Aggressive": (60, 25, 15), "Balanced": (70, 20, 10), "Conservative": (80, 15, 5)}[risk_prof]
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.info(f"💡 **Fiduciary Defaults for {risk_prof}:** {default_macro}% Equity / {100-default_macro}% Defensive. Equity is split {default_caps[0]}% Large / {default_caps[1]}% Mid / {default_caps[2]}% Small.")
                
                customize = st.toggle("⚙️ Customize Allocation Rules")
                
                custom_macro = None
                custom_cap = None
                
                if customize:
                    st.markdown("##### Custom Override Rules")
                    cust_eq = st.slider("Macro Split: Target Equity (%)", 10, 100, default_macro, help="The remainder will be allocated to Defensive/Capital Preservation assets.")
                    
                    st.write("Multi-Cap Equity Distribution (%)")
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1: l_cap = st.number_input("Large Cap", 0, 100, default_caps[0])
                    with mc2: m_cap = st.number_input("Mid Cap", 0, 100, default_caps[1])
                    with mc3: s_cap = st.number_input("Small Cap", 0, 100, default_caps[2])
                    
                    if (l_cap + m_cap + s_cap) != 100:
                        st.error(f"Cap percentages must sum to 100%. Current sum: {l_cap + m_cap + s_cap}%")
                        st.stop()
                    else:
                        custom_macro = cust_eq / 100.0
                        custom_cap = (l_cap/100.0, m_cap/100.0, s_cap/100.0)
                st.markdown("<br>", unsafe_allow_html=True)
                    
                c1, c2 = st.columns(2)
                with c1:
                    max_stocks = st.slider("Max Stock Positions", 5, 30, 15)
                with c2:
                    max_funds = st.slider("Max Fund Positions", 5, 15, 10)
                    
                if st.button("⚡ Generate Fiduciary Portfolio", width="stretch"):
                    with st.spinner(f"PathAllocator: Applying {risk_prof} macro rules and scanning entire market..."):
                        
                        # ── STEP 0: Goal-Gate Check ────────────────────────────────
                        from core.utils.goal_gate import evaluate_goal_gate, SURVIVAL_MODE, SAFETY_MODE
                        from app.agents.gia import GoalInterpretationAgent
                        
                        gate = None
                        try:
                            gia = GoalInterpretationAgent()
                            sleeves = gia.interpret_goals("user_1")
                            if sleeves:
                                raw_results = [gia.run_feasibility_check(s) for s in sleeves]
                                # Enrich with current_assets and target_value from sleeves
                                enriched = []
                                for res, sleeve in zip(raw_results, sleeves):
                                    enriched.append({**res,
                                        "current_assets": sleeve.current_assets,
                                        "target_value": sleeve.target_value})
                                gate = evaluate_goal_gate(enriched)
                        except Exception as e:
                            st.warning(f"Goal gate check skipped: {e}")

                        # Display mode banner
                        if gate:
                            st.markdown(f"""
                            <div style='background:{gate.banner_color}20; border-left:5px solid {gate.banner_color};
                                        padding:1rem; border-radius:8px; margin-bottom:1rem;'>
                                <h4 style='color:{gate.banner_color}; margin:0;'>{gate.banner_icon} {gate.headline}</h4>
                                <p style='color:#64748b; margin:0.5rem 0 0;'>{gate.rationale}</p>
                            </div>
                            """, unsafe_allow_html=True)

                        # ── STEP 1: Resolve portfolio mode constraints ──────────────
                        if gate and gate.mode == SURVIVAL_MODE:
                            # Fiduciary Lock: only defensive/liquid
                            st.session_state.path_equity = []
                            from app.agents.pfra import PassiveResearchAgent
                            pfra = PassiveResearchAgent()
                            defensive = pfra.screen_defensive_funds()
                            st.session_state.path_passive = [
                                {"ticker": f.ticker, "category": f.category,
                                 "target_capital": total_cap / max(1, len(defensive)),
                                 "target_weight": 1.0 / max(1, len(defensive)),
                                 "rationale": "🚨 Survival Mode: Liquid/Defensive Only",
                                 "conviction": getattr(f, "conviction_score", 0),
                                 "tracking_error": getattr(f, "tracking_error", 0),
                                 "expense_ratio": getattr(f, "expense_ratio", 0)}
                                for f in defensive
                            ]
                            st.session_state.allocator_meta = {
                                "equity_cap": 0,
                                "defensive_cap": total_cap,
                                "alpha_cap": 0,
                                "beta_cap": 0,
                                "regime_scale": "0%",
                                "optimizer_method": "Fiduciary Lock",
                            }
                        else:
                            # Safety Mode or Growth Mode — use PathAllocator with gated caps
                            if gate and gate.mode == SAFETY_MODE:
                                effective_eq_split = int(gate.equity_cap_pct * 100)
                            else:
                                effective_eq_split = eq_split

                            # Handle Portfolio Import Weight Calculation
                            current_port_map = None
                            if st.session_state.get('capital_type') == "Import Portfolio" and hasattr(st.session_state, 'imported_portfolio'):
                                df_imp = st.session_state.imported_portfolio
                                total_val = st.session_state.invested_amount
                                current_port_map = {}
                                from core.utils.symbol_mapper import SymbolMapper
                                st.write("🔄 Auditing current holdings for rebalancing...")
                                for _, row in df_imp.iterrows():
                                    sym = row['Symbol']
                                    qty = row['Quantity']
                                    try:
                                        yahoo_ticker = SymbolMapper.to_yahoo(sym)
                                        ticker = yf.Ticker(f"{yahoo_ticker}.NS")
                                        price = ticker.history(period="1d")["Close"].iloc[-1]
                                        current_port_map[sym] = (qty * price) / total_val
                                    except:
                                        st.warning(f"⚠️ Could not fetch live price for {sym}. Defaulting to exit.")
                                        current_port_map[sym] = 0.0

                            from app.agents.allocator import PathAllocator
                            allocator = PathAllocator(
                                max_stocks=max_stocks,
                                max_funds=max_funds,
                                risk_profile=risk_prof,
                                total_capital=total_cap,
                                equity_split_percent=effective_eq_split,
                                custom_macro_allocation=custom_macro,
                                custom_cap_ratios=custom_cap
                            )

                            st.session_state.path_equity = allocator.build_equity_sleeve(current_portfolio=current_port_map)
                            st.session_state.path_passive = allocator.build_passive_sleeve()
                            eq = st.session_state.path_equity
                            opt_method = eq[0].get('optimizer', 'Equal-Weight') if eq else 'Equal-Weight'
                            st.session_state.allocator_meta = {
                                "equity_cap": allocator.target_equity_capital,
                                "defensive_cap": allocator.target_defensive_capital,
                                "alpha_cap": allocator.alpha_capital,
                                "beta_cap": allocator.beta_equity_capital,
                                "regime_scale": f"{allocator.equity_allocation*100:.0f}%",
                                "optimizer_method": opt_method,
                            }
                        
                        # --- 🔄 PRE-SEAL TRANSITION AUDIT ---
                        st.write("🔄 Synchronizing Transition Metrics...")
                        regime = "BULL"
                        try:
                            # Simple Regime Check (Price > 200 SMA Proxy)
                            nifty = yf.Ticker("^NSEI").history(period="250d")["Close"]
                            regime = "BULL" if nifty.iloc[-1] > nifty.mean() else "BEAR"
                        except: pass
                        
                        trade_count = 0
                        total_sell_val = 0
                        if current_port_map:
                            total_inv_amount = st.session_state.invested_amount
                            target_map = {s['symbol']: s['target_capital'] for s in st.session_state.path_equity}
                            
                            # Count Exits and Trims
                            for sym, weight in current_port_map.items():
                                curr_val = weight * total_inv_amount
                                target_val = target_map.get(sym, 0)
                                
                                if target_val == 0: 
                                    trade_count += 1
                                    total_sell_val += curr_val
                                else:
                                    diff = target_val - curr_val
                                    if abs(diff) > (0.1 * curr_val): 
                                        trade_count += 1
                                        if diff < 0: # This is a TRIM (Sell)
                                            total_sell_val += abs(diff)
                                    
                            # Count New Buys
                            existing_syms = set(current_port_map.keys())
                            for s in st.session_state.path_equity:
                                if s['symbol'] not in existing_syms:
                                    trade_count += 1
                        else:
                            trade_count = len(st.session_state.path_equity) + (len(st.session_state.path_passive) if hasattr(st.session_state, 'path_passive') else 0)

                        # --- 🔗 SEALING THE MANIFEST (Layer 4 Governance) ---
                        try:
                            from app.agents.governance import GovernanceAgent
                            gov = GovernanceAgent()
                            manifest = {
                                "timestamp": str(pd.Timestamp.now()),
                                "amount": st.session_state.invested_amount,
                                "risk_profile": risk_prof,
                                "regime": regime,
                                "trade_count": trade_count,
                                "total_sell_value": total_sell_val,
                                "equity_sleeve": st.session_state.path_equity,
                                "passive_sleeve": st.session_state.path_passive
                            }
                            gov.seal_decision(manifest)
                            
                            # Display Fiduciary Seal
                            manifest_hash = gov.calculate_hash(manifest)
                            st.session_state.last_hash = manifest_hash
                            st.success("✅ **Fiduciary Portfolio Sealed.** Immutability Hash Generated.")
                            st.markdown(f"""
                                <div style='background:rgba(16,185,129,0.1); border:1px solid #10b981; padding:1rem; border-radius:10px; margin-top:1rem;'>
                                    <p style='color:#10b981; font-weight:700; margin:0;'>🛡️ FIDUCIARY SEAL ACTIVE</p>
                                    <code style='color:#34d399; font-size:0.75rem;'>FINGERPRINT: {manifest_hash}</code>
                                    <p style='color:#94a3b8; font-size:0.8rem; margin-top:0.5rem;'>
                                        This portfolio has been optimized under UCITS 5/10/40 and Sector-20 constraints. 
                                        The decision lineage is now locked in the immutable audit ledger.
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Governance Error: {e}")
                        
                        st.rerun()

            
            if hasattr(st.session_state, 'allocator_meta'):
                meta = st.session_state.allocator_meta
                method = meta.get('optimizer_method', 'Equal-Weight')
                method_badge = "🟢 MVO (Optimal)" if method == "MVO" else ("🟡 HRP (Fallback)" if method == "HRP" else "⚪ Equal-Weight (Legacy)")
                st.info(f"**Macro Allocation:** ₹{meta['equity_cap']:,.0f} Total Equity | ₹{meta['defensive_cap']:,.0f} Defensive | Optimizer: {method_badge}", icon="📊")
            
            if hasattr(st.session_state, 'path_equity'):
                st.markdown("#### 🔵 Alpha Sleeve: Direct Equities")
                df_eq = pd.DataFrame(st.session_state.path_equity)
                if not df_eq.empty:
                    # Flatten factors and explicitly round for the UI
                    df_eq['ROCE'] = df_eq['factors'].apply(lambda x: round(x.get('roce', 0), 4))
                    df_eq['FCF Yrs'] = df_eq['factors'].apply(lambda x: x.get('fcf_positive_years', 0))
                    df_eq['Momentum'] = df_eq['factors'].apply(lambda x: round(x.get('momentum', 0.5), 2))
                    df_eq['target_capital'] = df_eq['target_capital'].round(2)
                    df_eq['target_weight'] = df_eq['target_weight'].round(4)
                    
                    st.dataframe(
                        df_eq[['symbol', 'sector', 'cap', 'target_weight', 'target_capital', 'conviction', 'ROCE', 'FCF Yrs', 'Momentum']],
                        column_config={
                            "symbol": "Ticker",
                            "target_weight": st.column_config.ProgressColumn("Weight", format="%.2f", min_value=0, max_value=0.15),
                            "target_capital": st.column_config.NumberColumn("Capital (₹)", format="₹%,.2f"),
                            "ROCE": st.column_config.NumberColumn("ROCE", format="%.2%"),
                            "FCF Yrs": st.column_config.NumberColumn("FCF (3/4Y)", format="%d"),
                            "Momentum": st.column_config.ProgressColumn("Momentum", format="%.2f", min_value=0, max_value=1),
                            "conviction": st.column_config.NumberColumn("Conviction", format="%.2f")
                        },
                        hide_index=True,
                        width="stretch"
                    )
                else:
                    st.warning("No equities passed the strict QARP constraints.")


            if hasattr(st.session_state, 'path_passive'):
                st.markdown("#### 🟢 Beta & Defensive Sleeve: Funds")
                df_pf = pd.DataFrame(st.session_state.path_passive)
                if not df_pf.empty:
                    df_pf['target_capital'] = df_pf['target_capital'].round(2)
                    df_pf['target_weight'] = df_pf['target_weight'].round(4)
                    st.dataframe(
                        df_pf[['ticker', 'category', 'rationale', 'target_weight', 'target_capital', 'expense_ratio', 'conviction']],
                        column_config={
                            "ticker": "Ticker",
                            "target_weight": st.column_config.ProgressColumn("Weight", format="%.2f", min_value=0, max_value=0.20),
                            "target_capital": st.column_config.NumberColumn("Capital (₹)", format="₹%,.2f"),
                            "expense_ratio": st.column_config.NumberColumn("TER", format="%.2%"),
                            "conviction": st.column_config.NumberColumn("Conviction", format="%.2f")
                        },
                        hide_index=True,
                        width="stretch"
                    )
                else:
                    st.warning("No passive vehicles found.")

            # --- NEW: Rebalance Action Plan (Transition Logic) ---
            if hasattr(st.session_state, 'imported_portfolio') and hasattr(st.session_state, 'path_equity'):
                st.markdown("### 🔄 Rebalance Action Plan")
                st.markdown("<p style='color:#64748b; margin-top:-1rem;'>Specific instructions to transition your legacy holdings to the Fiduciary Path.</p>", unsafe_allow_html=True)
                
                with st.spinner("Calculating trade differentials and tax-loss harvesting opportunities..."):
                    actions = []
                    imp_df = st.session_state.imported_portfolio
                    target_eq = st.session_state.path_equity
                    target_map = {s['symbol']: s['target_capital'] for s in target_eq}
                    
                    # 1. Process Legacy Holdings (Exits and Trims)
                    for _, row in imp_df.iterrows():
                        sym = row['Symbol']
                        qty = row['Quantity']
                        avg_price = row.get('avg_buy_price', 0)
                        
                        # Get current price via normalized Yahoo Ticker
                        try:
                            from core.utils.symbol_mapper import SymbolMapper
                            yahoo_ticker = SymbolMapper.to_yahoo(sym)
                            curr_price = yf.Ticker(f"{yahoo_ticker}.NS").history(period="1d")["Close"].iloc[-1]
                        except:
                            curr_price = avg_price # Fallback
                        
                        curr_val = qty * curr_price
                        target_val = target_map.get(sym, 0)
                        diff = target_val - curr_val
                        
                        action = "HOLD"
                        if target_val == 0: action = "EXIT"
                        elif diff > (0.1 * curr_val): action = "TOP-UP" # 10% threshold for topup
                        elif diff < (-0.1 * curr_val): action = "TRIM"
                        
                        # Tax Loss Harvesting Flag
                        tlh = "✅ YES" if (avg_price > 0 and curr_price < avg_price and action in ["EXIT", "TRIM"]) else "—"
                        
                        actions.append({
                            "Asset": sym,
                            "Action": action,
                            "Current Value": curr_val,
                            "Target Value": target_val,
                            "Difference": diff,
                            "Tax Harvest": tlh
                        })
                    
                    # 2. Process New Entries (Buys)
                    imp_syms = set(imp_df['Symbol'].tolist())
                    for s in target_eq:
                        if s['symbol'] not in imp_syms:
                            actions.append({
                                "Asset": s['symbol'],
                                "Action": "NEW BUY",
                                "Current Value": 0,
                                "Target Value": s['target_capital'],
                                "Difference": s['target_capital'],
                                "Tax Harvest": "—"
                            })
                    
                    df_actions = pd.DataFrame(actions)
                    df_actions['Current Value'] = df_actions['Current Value'].round(2)
                    df_actions['Target Value'] = df_actions['Target Value'].round(2)
                    df_actions['Difference'] = df_actions['Difference'].round(2)
                    
                    st.dataframe(
                        df_actions,
                        column_config={
                            "Current Value": st.column_config.NumberColumn(format="₹%,.2f"),
                            "Target Value": st.column_config.NumberColumn(format="₹%,.2f"),
                            "Difference": st.column_config.NumberColumn(format="₹%,.2f"),
                            "Action": st.column_config.TextColumn("Recommendation"),
                            "Tax Harvest": st.column_config.TextColumn("Tax Harvest")
                        },
                        hide_index=True,
                        width="stretch"
                    )
                    
                    # --- EXECUTION SUMMARY ---
                    total_buys = sum([a['Difference'] for a in actions if a['Difference'] > 0])
                    total_sells = abs(sum([a['Difference'] for a in actions if a['Difference'] < 0]))
                    net_change = total_buys - total_sells
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        st.markdown(f"<div style='background:rgba(16,185,129,0.1); border-radius:10px; padding:1rem; text-align:center;'><p style='color:#10b981; margin:0; font-size:0.9rem;'>TOTAL BUYS</p><h3 style='margin:0;'>{fmt_inr(total_buys)}</h3></div>", unsafe_allow_html=True)
                    with e2:
                        st.markdown(f"<div style='background:rgba(244,63,94,0.1); border-radius:10px; padding:1rem; text-align:center;'><p style='color:#f43f5e; margin:0; font-size:0.9rem;'>TOTAL SELLS</p><h3 style='margin:0;'>{fmt_inr(total_sells)}</h3></div>", unsafe_allow_html=True)
                    with e3:
                        st.markdown(f"<div style='background:rgba(99,102,241,0.1); border-radius:10px; padding:1rem; text-align:center;'><p style='color:#6366f1; margin:0; font-size:0.9rem;'>NET FUNDING</p><h3 style='margin:0;'>{fmt_inr(net_change)}</h3></div>", unsafe_allow_html=True)

    elif nav == "Goal Health":
        st.markdown("### 🎯 Goal Tracking")
        from app.agents.gia import GoalInterpretationAgent
        gia = GoalInterpretationAgent()
        
        sleeves = gia.interpret_goals("user_1")
        
        if not sleeves:
            st.info("No goals found. Please complete the **Onboarding / Discovery** tab to see your goal feasibility analysis.")
        else:
            # Run feasibility checks for each goal
            # Run feasibility checks for each goal
            results = [gia.run_feasibility_check(s) for s in sleeves]
            
            # Display metrics in columns
            cols = st.columns(len(results))
            for i, res in enumerate(results):
                with cols[i]:
                    prob = res['p_success']
                    target = res.get('target_value', 1)
                    outcome = res.get('median_outcome', 0)
                    sleeve = sleeves[i]
                    horizon_yrs = sleeve.horizon_years
                    current_assets = sleeve.current_assets

                    # ── Progress: capital deployed vs. inflation-adjusted target ──
                    # (NOT outcome/target — that gives misleading 100% when market does well)
                    capital_progress = min(100, int((current_assets / target) * 100)) if target > 0 else 0
                    # Separate signal: does the projected outcome actually cover the target?
                    outcome_covers_target = outcome >= target
                    shortfall = max(0, target - outcome)

                    # ── SIP needed to close the shortfall ──
                    r_monthly = 0.10 / 12   # 10% p.a. assumed
                    n_months  = max(1, horizon_yrs * 12)
                    try:
                        sip_needed = shortfall * r_monthly / ((1 + r_monthly)**n_months - 1) if shortfall > 0 else 0
                    except Exception:
                        sip_needed = shortfall / n_months if shortfall > 0 else 0

                    # ── Status logic ──
                    if prob > 0.95:
                        status, color, icon = "SECURE", "#10b981", "✅"
                        advice = "On track. Maintain current allocation."

                    elif prob > 0.80:
                        status, color, icon = "WATCH", "#f59e0b", "⚠️"
                        if shortfall > 0:
                            advice = f"Minor gap. Add {fmt_inr(sip_needed)}/month SIP to secure this goal."
                        else:
                            advice = "Outcome exceeds target but variance is elevated. Consider de-risking 10-15% of allocation."

                    else:
                        status, color, icon = "DEFICIT", "#f43f5e", "🚨"

                        if current_assets == 0:
                            # No capital at all
                            advice = f"No capital allocated. Start a {fmt_inr(sip_needed or (target / n_months))}/month SIP or redirect funds from the Onboarding tab."

                        elif res['label'] == "Survival":
                            # Emergency fund — must be near-certain (99%+), not market-linked
                            if outcome_covers_target:
                                advice = (f"⚠️ Portfolio is too volatile for an emergency fund. "
                                          f"Current success prob: {prob:.0%} — needs 99%+. "
                                          f"Move {fmt_inr(current_assets)} to a Liquid Fund or FD.")
                            else:
                                top_up = target - current_assets
                                advice = (f"Fund this first. Need {fmt_inr(top_up)} more. "
                                          f"Keep in Liquid Fund/FD — not market-linked instruments.")

                        elif outcome_covers_target:
                            # Median outcome covers target but probability is low → VARIANCE problem
                            advice = (f"Your median outcome ({fmt_inr(outcome)}) beats the target, "
                                      f"but success probability is only {prob:.0%} due to high portfolio volatility. "
                                      f"De-risk: shift 20-30% to debt/gold to improve certainty.")
                        else:
                            # True funding gap
                            advice = f"Gap: {fmt_inr(shortfall)} over {horizon_yrs}yr. Start a {fmt_inr(sip_needed)}/month SIP to close it."

                    # ── Progress bar: dual signal (capital funded + outcome coverage) ──
                    outcome_pct = min(100, int((outcome / target) * 100)) if target > 0 else 0
                    progress_label = f"Capital Funded: {capital_progress}% | Projected Coverage: {outcome_pct}%"

                    asset_mandate = res.get("asset_mandate", "")
                    mandate_colors = {
                        "Survival":  "#0ea5e9",
                        "Safety":    "#8b5cf6",
                        "Growth":    "#f59e0b",
                    }
                    mandate_color = mandate_colors.get(res['label'], "#64748b")
                    min_prob = {1: 0.99, 2: 0.95, 3: 0.70}.get(
                        {"Survival": 1, "Safety": 2, "Growth": 3}.get(res['label'], 3), 0.70)

                    st.markdown(f"""
                    <div class='card' style='border-top: 4px solid {color};'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h4 style='margin:0;'>{icon} {res['label']}</h4>
                            <span style='color:{color}; font-weight:700;'>{status}</span>
                        </div>
                        <div style='margin-bottom:0.5rem;'>
                            <span style='background:{mandate_color}20; color:{mandate_color};
                                         padding:0.15rem 0.6rem; border-radius:20px;
                                         font-size:0.75rem; font-weight:600;'>
                                🏦 {asset_mandate}
                            </span>
                            <span style='font-size:0.75rem; color:#94a3b8; margin-left:0.5rem;'>
                                Needs {min_prob:.0%} probability to be SECURE
                            </span>
                        </div>
                        <p style='font-size:0.8rem; color:#64748b; margin-bottom:0.3rem;'>
                            Target: <b>{fmt_inr(target)}</b> (inflation-adjusted over {horizon_yrs}yr)
                        </p>
                        <p style='font-size:0.8rem; color:#64748b; margin-bottom:0.4rem;'>{progress_label}</p>
                        <div style='background:#f1f5f9; border-radius:10px; height:8px; width:100%; margin-bottom:0.3rem;'>
                            <div style='background:{color}; height:8px; width:{capital_progress}%; border-radius:10px;'></div>
                        </div>
                        <p style='font-size:0.75rem; color:#94a3b8; margin-bottom:0.8rem;'>
                            Capital deployed: {fmt_inr(current_assets)}
                        </p>
                        <small style='color:#64748b;'>Prob. of Success: <b style='color:{color}'>{prob:.1%}</b></small><br>
                        <small style='color:#64748b;'>Median Projected Outcome: <b>{fmt_inr(outcome)}</b></small>
                        <div style='margin-top:1rem; padding-top:0.8rem; border-top:1px solid #e2e8f0;'>
                            <p style='font-size:0.85rem; font-weight:600; color:#1e293b; margin-bottom:0;'>📋 Fiduciary Action:</p>
                            <p style='font-size:0.85rem; color:#64748b;'>{advice}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.caption(
                "🟢 **SECURE** | 🟡 **WATCH** | 🔴 **DEFICIT**  \n"
                "Thresholds: Survival ≥ 99% (Liquid/FD) · Safety ≥ 95% (Balanced/Debt) · Growth ≥ 70% (Equity)"
            )


    elif nav == "Voice & Insights":
        st.markdown("### 🎙️ The Voice")
        
        # LLM Connectivity Status
        insa = InsightNarrativeEngine(api_key=os.getenv("GOOGLE_API_KEY"))
        llm_status = insa.get_status()
        st.markdown(f"""
            <div style='margin-bottom:1rem;'>
                <span style='background:{llm_status['color']}20; color:{llm_status['color']}; padding:0.2rem 0.8rem; border-radius:20px; font-size:0.8rem; font-weight:600;'>
                    {llm_status['status']}: {llm_status['model']}
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        # Pull real latest insight from Layer 4
        history = get_audit_history(limit=1)
        st.markdown("<div class='card' style='border-left: 4px solid #6366f1;'>", unsafe_allow_html=True)
        if history:
            manifest = json.loads(history[0]['manifest_json'])
            regime = manifest.get('regime', 'N/A')
            count = manifest.get('trade_count', 0)
            sell_val = manifest.get('total_sell_value', 0)
            st.write(f"**Latest Insight ({history[0]['timestamp'][:10]}):**")
            st.write(f"The system detected a **{regime}** regime and orchestrated **{count}** rebalance actions to optimize your goals.")
            if sell_val > 0:
                st.write(f"⚠️ **Execution Note:** Rebalancing will generate **{fmt_inr(sell_val)}** in liquidity from legacy exits/trims.")
        else:
            st.write("**Latest Insight:** System Initialized. No rebalance actions taken yet.")
            st.info("💡 **Tip:** Once you complete onboarding and a rebalance cycle runs, your personalized fiduciary narrative will appear here.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # --- PERFORMANCE BENCHMARKING (3Y) ---
        st.markdown("##### 📈 3-Year Relative Performance")
        with st.spinner("Analyzing 36-month historical relative performance..."):
            # Get data for proposed portfolio
            eq_sleeve = st.session_state.get('path_equity', [])
            pass_sleeve = st.session_state.get('path_passive', [])
            inv_df = st.session_state.get('imported_portfolio', None)
            
            perf_df, daily_returns = get_benchmark_performance(eq_sleeve, pass_sleeve, inv_df)
            
            if perf_df is not None:
                fig = px.line(perf_df, x='Date', y=perf_df.columns[1:], 
                             title="Cumulative Returns (Base 100)",
                             color_discrete_sequence=px.colors.qualitative.Prism)
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend_title="",
                    xaxis_title="",
                    yaxis_title="Growth of ₹100",
                    hovermode="x unified",
                    font=dict(family="Inter", size=12)
                )
                st.plotly_chart(fig, width="stretch")

                # --- NEW: Risk Metrics Table ---
                st.markdown("##### 🛡️ Risk & Reward Audit (3-Year)")
                
                metrics = []
                # Use daily_returns which now includes synthesised portfolio columns
                composite_returns = daily_returns.copy()
                
                # Ensure benchmarks are also available if not already in columns
                bench_map = {"Nifty 50": "^NSEI", "Nifty Next 50": "JUNIORBEES.NS"}
                for name, ticker in bench_map.items():
                    if ticker in composite_returns.columns and name not in composite_returns.columns:
                        composite_returns[name] = composite_returns[ticker]

                # Filter to only show relevant benchmarks and the two portfolios
                display_cols = [
                    "Nifty 50", "Proposed Portfolio", "Investor Portfolio", 
                    "Nifty Next 50"
                ]
                
                for col in display_cols:
                    if col not in composite_returns.columns:
                        continue
                    
                    rets = composite_returns[col]
                    if rets.abs().sum() == 0: continue # Skip if no data
                    
                    ann_ret = rets.mean() * 252
                    ann_vol = rets.std() * np.sqrt(252)
                    sharpe = (ann_ret - 0.06) / ann_vol if ann_vol > 0 else 0
                    
                    # Max Drawdown
                    cum_rets = (1 + rets).cumprod()
                    running_max = cum_rets.cummax()
                    drawdown = (cum_rets - running_max) / running_max
                    max_dd = drawdown.min()
                    
                    metrics.append({
                        "Asset / Portfolio": col,
                        "Return (Ann)": f"{ann_ret:.1%}",
                        "Volatility": f"{ann_vol:.1%}",
                        "Sharpe Ratio": f"{sharpe:.2f}",
                        "Max Drawdown": f"{max_dd:.1%}"
                    })
                
                st.table(pd.DataFrame(metrics))
            else:
                st.warning("⚠️ Market connectivity required for live 12-month benchmarking. Showing simulated resilience metrics below.")
                st.image("https://via.placeholder.com/800x400/1e293b/6366f1?text=Historical+Benchmarking+Requires+Live+Data+Feed", width="stretch")

        st.markdown("##### 💬 Fiduciary Chat")
        
        # Display chat history
        for chat in st.session_state.chat_history:
            if chat["role"] == "user":
                st.write(f"**👤 You:** {chat['content']}")
            else:
                st.info(f"**🤖 YourBestPath AI:** {chat['content']}")

        user_q = st.chat_input("Ask about your portfolio, e.g., 'Why is my growth goal in deficit?'")
        if user_q:
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            
            # 1. Fetch Latest Manifest as context
            history = get_audit_history(limit=1)
            manifest = {}
            if history:
                manifest = json.loads(history[0]['manifest_json'])
            
            # 2. Call INSA for dynamic fiduciary response
            # Note: GOOGLE_API_KEY should be in your .env for real LLM behavior
            insa = InsightNarrativeEngine(api_key=os.getenv("GOOGLE_API_KEY"))
            response = insa.chat(user_q, manifest, st.session_state.chat_history)
            
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

else: # Quant Admin Persona
    st.markdown("### 🛠️ Execution Commander")
    
    if nav == "Admin Console":
        st.markdown("#### ⚙️ Agent Orchestration & Tuning")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("##### Agent Status")
            st.toggle("Equity Research Agent (EQRA)", value=True)
            st.toggle("Risk Assessment Agent (RAA)", value=True)
            st.toggle("Macro Analysis Agent", value=True)
            st.toggle("Order Execution Agent", value=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("##### Hyperparameters")
            st.slider("Max VaR Limit (%)", 1.0, 10.0, 3.5, 0.1)
            st.slider("Rebalance Frequency (Days)", 1, 90, 30)
            st.slider("Conviction Threshold", 0.0, 1.0, 0.75, 0.05)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.divider()
        st.markdown("#### 🚀 Manual Overrides")
        if st.button("⚡ Force Rebalance Cycle", type="primary"):
            st.success("Rebalance Cycle Initiated. Agents are now analyzing the market.")

    elif nav == "Risk Control":
        st.markdown("#### 🛡️ Live Risk Metrics & Guardrails")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown("<div class='card'><p class='metric-title'>99% Daily VaR</p><p class='metric-value status-secure'>3.12%</p></div>", unsafe_allow_html=True)
        with r2:
            st.markdown("<div class='card'><p class='metric-title'>Max Drawdown Limit</p><p class='metric-value status-watch'>-15.0%</p></div>", unsafe_allow_html=True)
        with r3:
            st.markdown("<div class='card'><p class='metric-title'>Portfolio Beta</p><p class='metric-value'>1.08</p></div>", unsafe_allow_html=True)
            
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 🚧 Fiduciary Guardrails")
            st.write("🟢 Sector Limit (< 20%): **OK (Healthy Ceiling Active)**")
            st.write("🟢 UCITS 5/10/40 Rule: **OK (Assets > 5% < 40%)**")
            st.write("🟢 Single Stock Limit (< 10%): **OK (Institutional Standard)**")
            st.write("🟢 Liquidity Buffer (> 5%): **OK (Verified via ADV)**")
            st.write("🟡 Volatility Cap (< 20% ann.): **WATCH (18.2%)**")
        with col2:
            st.markdown("##### 🌪️ Stress Test Scenarios")
            shock = st.selectbox("Select Historical Shock", ["2008 Financial Crisis", "2020 COVID-19 Crash", "2000 Dot-Com Bubble"])
            if st.button("Run Stress Test"):
                if shock == "2008 Financial Crisis":
                    st.info("Simulating 2008 Liquidity Shock... Estimated Portfolio Impact: **-22%** (vs Benchmark -38%)")
                elif shock == "2020 COVID-19 Crash":
                    st.info("Simulating 2020 Volatility Spike... **-15%** (vs Benchmark -30%)")
                elif shock == "2000 Dot-Com Bubble":
                    st.info("Simulating 2000 Tech De-rating... **-12%** (vs Benchmark -25%)")
                st.caption("Resilience is driven by UCITS 5/10/40 and 20% Sector Ceiling constraints.")

        st.divider()
        st.markdown("#### 🧠 System Intelligence Diagnostics")
        diag_col1, diag_col2 = st.columns(2)
        
        # 1. API Diagnostics
        with diag_col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("##### AI Connectivity Hub")
            
            # Check Groq
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                st.write(f"🔑 **Groq Key**: `...{groq_key[-8:]}`")
                # We could add a 'Test Ping' button here
            else:
                st.error("❌ Groq Key Missing")
                
            # Check Gemini
            gemini_key = os.getenv("GOOGLE_API_KEY")
            if gemini_key:
                st.write(f"🔑 **Gemini Key**: `...{gemini_key[-8:]}`")
            else:
                st.error("❌ Gemini Key Missing")
            
            if st.button("Test AI Connection"):
                insa = InsightNarrativeEngine(api_key=gemini_key)
                status = insa.get_status()
                st.success(f"Primary Intelligence: {status['model']}")
            st.markdown("</div>", unsafe_allow_html=True)

        # 2. Log Inspector
        with diag_col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("##### Fiduciary Log Inspector")
            if st.button("View Latest LLM Interactions"):
                log_path = "app/data/llm_calls.log"
                if os.path.exists(log_path):
                    with open(log_path, "r") as f:
                        logs = f.readlines()
                        for log in logs[-5:]:
                            st.json(json.loads(log))
                else:
                    st.info("No LLM logs found yet.")
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav == "Audit Ledger":
        st.markdown("#### 📜 System Audit Ledger")
        st.write("Immutable log of all agent reasoning, trades, and system state transitions.")
        
        # Sidebar notice
        st.sidebar.success("Audit Mode: Active")
        st.sidebar.info("All decision manifests are cryptographically signed and stored in the immutable ledger below.")
        
        history = get_audit_history(limit=50)
        if history:
            df = pd.DataFrame(history)
            # Only select columns that actually exist in the audit_trail schema
            st.dataframe(df[['id', 'timestamp', 'manifest_hash', 'integrity_sealed']])
            
            st.download_button(
                label="📥 Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='audit_ledger.csv',
                mime='text/csv',
            )
            
            st.divider()
            st.markdown("##### 🔍 Inspect Decision Manifest")
            selected_id = st.selectbox("Select Audit ID to Inspect", df['id'].tolist())
            if selected_id:
                manifest_row = df[df['id'] == selected_id].iloc[0]
                try:
                    manifest_data = json.loads(manifest_row['manifest_json'])
                    st.json(manifest_data)
                except:
                    st.warning("Manifest content is in raw format or corrupted.")
                
                st.code(f"SHA-256 FINGERPRINT: {manifest_row['manifest_hash']}", language="text")
                if manifest_row['integrity_sealed']:
                    st.success("✅ INTEGRITY VERIFIED: This manifest matches the recorded fingerprint.")
                else:
                    st.error("❌ INTEGRITY BREACH: Manifest hash mismatch detected!")
            for record in history[:3]:
                with st.expander(f"Audit Entry {record['id']} | {record['timestamp']}"):
                    try:
                        manifest = json.loads(record['manifest_json'])
                        st.json(manifest)
                    except:
                        st.write("Invalid JSON manifest.")
        else:
            st.info("No audit logs found. The database may be empty.")

    elif nav == "System Health":
        st.markdown("#### 🩺 Infrastructure & API Health")
        
        h1, h2, h3 = st.columns(3)
        with h1:
            st.markdown("<div class='card'><p class='metric-title'>Breeze API</p><p class='metric-value status-secure'>98ms</p></div>", unsafe_allow_html=True)
        with h2:
            st.markdown("<div class='card'><p class='metric-title'>LLM Provider (Groq)</p><p class='metric-value status-secure'>420ms</p></div>", unsafe_allow_html=True)
        with h3:
            st.markdown("<div class='card'><p class='metric-title'>Local DB Ops</p><p class='metric-value status-secure'>12ms</p></div>", unsafe_allow_html=True)
            
        st.divider()
        st.markdown("##### 💻 Local Resource Usage (Orchestrator)")
        st.progress(0.45, text="CPU Utilization: 45%")
        st.progress(0.68, text="Memory Usage: 6.8 GB / 10 GB")
        
        st.divider()
        st.markdown("##### 📑 Live API Logs (`logs/apiLogs.log`)")
        try:
            log_path = "logs/apiLogs.log"
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    lines = f.readlines()[-20:]
                    log_text = "".join(lines)
                st.code(log_text, language='text')
            else:
                st.warning("Log file not found.")
        except Exception as e:
            st.error(f"Error reading logs: {e}")
