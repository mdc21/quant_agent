"""
YourBestPath — Quick Investment Advice (4-Question Flow)
For users who want investment guidance without defining full goals.
Captures: Purpose, Horizon, Risk, Amount (Lump Sum + SIP)
"""
import logging
import streamlit as st

logger = logging.getLogger(__name__)

def render_quick_advice():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'Inter',sans-serif;}
    .stApp{background:#f8fafc;}
    .qa-title{font-size:1.6rem;font-weight:800;color:#1e293b;margin-bottom:0.2rem;}
    .qa-sub{color:#64748b;font-size:0.9rem;margin-bottom:2rem;}
    .q-card{
        background:white;border:1.5px solid #e2e8f0;border-radius:14px;
        padding:1.4rem 1.6rem;margin-bottom:1.2rem;
        box-shadow:0 2px 8px rgba(0,0,0,0.04);
    }
    .q-label{font-weight:700;color:#1e293b;font-size:1rem;margin-bottom:1rem;}
    .pill-row{display:flex;flex-wrap:wrap;gap:0.6rem;}
    .pill{
        padding:0.4rem 1.1rem;border-radius:20px;border:1.5px solid #e2e8f0;
        font-size:0.85rem;font-weight:500;cursor:pointer;background:white;color:#475569;
    }
    .pill.active{border-color:#6366f1;background:rgba(99,102,241,0.12);color:#6366f1;font-weight:700;}
    .risk-card{
        border:2px solid #e2e8f0;border-radius:12px;padding:1rem;text-align:center;
        cursor:pointer;background:white;
    }
    .risk-card.active{border-color:#6366f1;background:rgba(99,102,241,0.08);}
    div.stButton>button{
        border-radius:10px!important;font-weight:600!important;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("← Back to Home", key="qa_back_home"):
        st.session_state.app_page = "home"
        st.rerun()

    st.markdown("<div class='qa-title'>Get Personalised Investment Advice</div>", unsafe_allow_html=True)
    st.markdown("<div class='qa-sub'>Answer 4 quick questions — takes 2 minutes.</div>", unsafe_allow_html=True)

    # ── Q1: Purpose ──────────────────────────────────────────────
    PURPOSES = ["Wealth Growth", "Regular Income", "Tax Saving", "Capital Preservation"]
    sel_purpose = st.session_state.get("qa_purpose", None)

    st.markdown("<div class='q-card'>", unsafe_allow_html=True)
    st.markdown("<div class='q-label'>1. What is the purpose of this investment?</div>", unsafe_allow_html=True)
    cols = st.columns(len(PURPOSES))
    for i, p in enumerate(PURPOSES):
        with cols[i]:
            is_sel = sel_purpose == p
            if st.button(("✓ " if is_sel else "") + p, key=f"qa_p_{i}", use_container_width=True):
                st.session_state.qa_purpose = p
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Q2: Investment Horizon ───────────────────────────────────
    HORIZONS = ["< 1 Year", "1–3 Years", "3–7 Years", "7–15 Years", "15+ Years"]
    sel_hz = st.session_state.get("qa_horizon", "3–7 Years")

    st.markdown("<div class='q-card'>", unsafe_allow_html=True)
    st.markdown("<div class='q-label'>2. What is your investment horizon?</div>", unsafe_allow_html=True)
    hz_idx = HORIZONS.index(sel_hz) if sel_hz in HORIZONS else 2
    new_hz = st.select_slider("", options=HORIZONS, value=HORIZONS[hz_idx], key="qa_hz_slider",
                               label_visibility="collapsed")
    if new_hz != sel_hz:
        st.session_state.qa_horizon = new_hz
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Q3: Risk Appetite ────────────────────────────────────────
    RISKS = [
        {"id": "Conservative", "icon": "🛡️", "sub": "Low returns · Stable"},
        {"id": "Moderate",     "icon": "⚖️", "sub": "Balanced risk-return"},
        {"id": "Aggressive",   "icon": "🚀", "sub": "High returns · Higher risk"},
    ]
    sel_risk = st.session_state.get("qa_risk", "Moderate")

    st.markdown("<div class='q-card'>", unsafe_allow_html=True)
    st.markdown("<div class='q-label'>3. What is your risk appetite?</div>", unsafe_allow_html=True)
    r_cols = st.columns(3)
    for i, r in enumerate(RISKS):
        with r_cols[i]:
            is_sel = sel_risk == r["id"]
            border = "#6366f1" if is_sel else "#e2e8f0"
            bg = "rgba(99,102,241,0.08)" if is_sel else "white"
            st.markdown(f"""
            <div style='border:2px solid {border};border-radius:12px;padding:1rem;
                text-align:center;background:{bg};margin-bottom:0.5rem;'>
                <div style='font-size:1.8rem;'>{r["icon"]}</div>
                <div style='font-weight:700;font-size:0.9rem;color:#1e293b;'>{r["id"]}</div>
                <div style='font-size:0.72rem;color:#94a3b8;'>{r["sub"]}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{'✓ ' if is_sel else ''}{r['id']}", key=f"qa_r_{i}", use_container_width=True):
                st.session_state.qa_risk = r["id"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Q4: Investment Amount ────────────────────────────────────
    st.markdown("<div class='q-card'>", unsafe_allow_html=True)
    st.markdown("<div class='q-label'>4. How would you like to invest?</div>", unsafe_allow_html=True)
    col_lump, col_sip = st.columns(2)
    with col_lump:
        lump = st.number_input("One-time Lump Sum (₹)", min_value=0,
                               value=st.session_state.get("qa_lump", 0),
                               step=100000, format="%d", key="qa_lump_input")
        st.session_state.qa_lump = lump
    with col_sip:
        sip = st.number_input("Monthly SIP (₹)", min_value=0,
                              value=st.session_state.get("qa_sip", 0),
                              step=5000, format="%d", key="qa_sip_input")
        st.session_state.qa_sip = sip
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Generate Plan ────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ Generate My Investment Plan →", key="qa_generate", use_container_width=True):
        purpose  = st.session_state.get("qa_purpose")
        horizon  = st.session_state.get("qa_horizon", "3–7 Years")
        risk     = st.session_state.get("qa_risk", "Moderate")
        lump_val = st.session_state.get("qa_lump", 0)
        sip_val  = st.session_state.get("qa_sip", 0)

        logger.info(f"Quick Advice Generation attempt: Purpose='{purpose}', Risk='{risk}', LumpSum={lump_val}, SIP={sip_val}")

        if not purpose:
            st.warning("Please select a purpose for your investment.")
            return
        if lump_val == 0 and sip_val == 0:
            st.warning("Please enter a lump sum or monthly SIP amount.")
            return

        # Store as session state for dashboard to use
        st.session_state.invested_amount = lump_val + (sip_val * 12)
        st.session_state.user_risk_profile = risk
        st.session_state.qa_mode = True
        st.session_state.qa_summary = {
            "purpose": purpose, "horizon": horizon, "risk": risk,
            "lump_sum": lump_val, "sip_monthly": sip_val,
            "total_annual": lump_val + (sip_val * 12)
        }

        # Show allocation preview before routing
        _show_allocation_preview(purpose, risk, horizon, lump_val, sip_val)


def _show_allocation_preview(purpose, risk, horizon, lump, sip):
    """Show a smart asset allocation recommendation before routing to dashboard."""

    ALLOCATIONS = {
        ("Wealth Growth",        "Aggressive"):   {"Equities": 80, "Passive/ETF": 15, "Debt": 5},
        ("Wealth Growth",        "Moderate"):     {"Equities": 60, "Passive/ETF": 20, "Debt": 20},
        ("Wealth Growth",        "Conservative"): {"Equities": 40, "Passive/ETF": 20, "Debt": 40},
        ("Regular Income",       "Aggressive"):   {"Equities": 40, "Debt": 40, "REITs/InvIT": 20},
        ("Regular Income",       "Moderate"):     {"Equities": 20, "Debt": 60, "REITs/InvIT": 20},
        ("Regular Income",       "Conservative"): {"Debt": 70, "FD/GOI Bonds": 20, "Cash": 10},
        ("Tax Saving",           "Aggressive"):   {"ELSS": 80, "NPS Equity": 20},
        ("Tax Saving",           "Moderate"):     {"ELSS": 50, "NPS": 30, "PPF": 20},
        ("Tax Saving",           "Conservative"): {"PPF": 50, "NPS Debt": 30, "GOI Bonds": 20},
        ("Capital Preservation", "Aggressive"):   {"Debt": 50, "Equities": 30, "Gold": 20},
        ("Capital Preservation", "Moderate"):     {"Debt": 60, "Gold": 25, "Cash": 15},
        ("Capital Preservation", "Conservative"): {"Debt": 70, "Gold": 20, "Cash": 10},
    }

    key = (purpose, risk)
    alloc = ALLOCATIONS.get(key, {"Equities": 50, "Debt": 30, "Cash": 20})
    total = lump + (sip * 12)

    colors = ["#6366f1", "#10b981", "#f59e0b", "#3b82f6", "#ec4899"]
    st.markdown("---")
    st.markdown("### 📊 Recommended Asset Allocation")
    st.markdown(f"Based on your **{purpose}** goal with **{risk}** risk appetite over **{horizon}**:")

    cols = st.columns(len(alloc))
    for i, (asset, pct) in enumerate(alloc.items()):
        with cols[i]:
            val = total * pct / 100
            st.markdown(f"""
            <div style='background:{colors[i % len(colors)]}15;border:1.5px solid {colors[i % len(colors)]};
                border-radius:12px;padding:1rem;text-align:center;'>
                <div style='font-size:1.4rem;font-weight:800;color:{colors[i % len(colors)]};'>{pct}%</div>
                <div style='font-weight:600;font-size:0.85rem;color:#1e293b;'>{asset}</div>
                <div style='font-size:0.75rem;color:#64748b;'>
                    {"₹" + f"{val/1e5:.1f}L" if val >= 1e5 else "₹" + f"{val:,.0f}"}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Open Full Fiduciary Dashboard →", key="qa_to_dashboard", use_container_width=True):
        logger.info("Quick Advice path routing to full dashboard")
        st.session_state.app_page = "dashboard"
        st.rerun()
