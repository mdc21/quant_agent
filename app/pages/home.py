"""
YourBestPath — Post-Login Home Page
Shows the user's wealth snapshot and routes them to the correct path:
1. Define Goals (first-time wizard)
2. Review & Update Goals (returning user)
3. Get Investment Advice (quick one-time/SIP path)
"""
import logging
import streamlit as st
import plotly.graph_objects as go
from core.data.store import DataStore
from core.auth.user_store import UserStore

logger = logging.getLogger(__name__)

def _fmt_inr(val: float) -> str:
    if val >= 1e7:
        return f"₹{val/1e7:.2f}Cr"
    elif val >= 1e5:
        return f"₹{val/1e5:.2f}L"
    return f"₹{val:,.0f}"


def _asset_donut(distribution: dict) -> go.Figure:
    """Renders the asset class distribution donut chart."""
    labels = list(distribution.keys())
    values = list(distribution.values())
    colors = ["#6366f1", "#10b981", "#f59e0b", "#3b82f6", "#ec4899"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.62,
        marker_colors=colors[:len(labels)],
        textinfo="label+percent",
        textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value:.1f}%<extra></extra>"
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=220,
    )
    return fig


def render_home():
    """Main post-login home page."""

    # ── CSS ─────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0f172a; color: #e2e8f0; }

    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin: 1.2rem 0;
    }
    .kpi-tile {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 1rem 1.2rem;
        backdrop-filter: blur(12px);
    }
    .kpi-label { font-size: 0.75rem; color: #94a3b8; font-weight: 500; margin-bottom:0.3rem; }
    .kpi-value { font-size: 1.3rem; font-weight: 800; color: #f1f5f9; }

    .panel {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.4rem;
        backdrop-filter: blur(8px);
        height: 100%;
    }
    .panel-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 1rem;
    }

    .goal-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
    }
    .goal-label { font-size: 0.85rem; font-weight: 600; }
    .goal-meta  { font-size: 0.75rem; color: #94a3b8; }
    .goal-amount{ font-size: 0.85rem; font-weight: 700; }
    .progress-bar {
        height: 6px;
        border-radius: 999px;
        margin-top: 0.3rem;
    }

    .action-section { margin-top: 2rem; }
    .action-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 1.2rem;
    }
    .action-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.2rem;
    }
    .action-card {
        border-radius: 16px;
        padding: 1.8rem 1.2rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        border: 1.5px solid;
    }
    .action-card:hover { transform: translateY(-3px); }
    .action-card .icon { font-size: 2.2rem; margin-bottom: 0.7rem; }
    .action-card .label { font-size: 1rem; font-weight: 700; }
    .action-card .desc  { font-size: 0.78rem; color: #94a3b8; margin-top:0.3rem; }

    .card-indigo { background: rgba(99,102,241,0.15); border-color: #6366f1; }
    .card-teal   { background: rgba(20,184,166,0.15); border-color: #14b8a6; }
    .card-amber  { background: rgba(245,158,11,0.15); border-color: #f59e0b; }
    </style>
    """, unsafe_allow_html=True)

    user_name = st.session_state.get("user_name", "Investor")
    user_key = st.session_state.get("user_key", "user_1")

    # ── Greeting ────────────────────────────────────────────────
    import datetime
    hour = datetime.datetime.now().hour
    greeting = "Good Morning" if hour < 12 else ("Good Afternoon" if hour < 17 else "Good Evening")

    st.markdown(f"""
    <div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.5rem;'>
        <div>
            <h2 style='margin:0; font-size:1.8rem; color:#f1f5f9;'>{greeting}, {user_name} 👋</h2>
            <p style='margin:0; color:#64748b; font-size:0.85rem;'>
                {datetime.datetime.now().strftime("%A, %d %B %Y")}
            </p>
        </div>
        <div style='text-align:right;'>
            <span style='background:#6366f1; color:white; border-radius:20px; padding:0.3rem 0.8rem; font-size:0.75rem; font-weight:600;'>
                🛡️ FIDUCIARY ENGINE ACTIVE
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load user data ───────────────────────────────────────────
    try:
        ds = DataStore()
        goals_data = ds.get_goals(user_key)
        goals = goals_data.get("goals", [])
        risk_profile = goals_data.get("risk_tolerance",
                        st.session_state.get("user_risk_profile", "Moderate"))
        inflation_rate = goals_data.get("inflation_rate", 0.06)
    except Exception:
        goals = []
        risk_profile = st.session_state.get("user_risk_profile", "Moderate")
        inflation_rate = 0.06

    # Load imported portfolio for asset distribution
    imported_df = st.session_state.get("imported_portfolio")
    total_wealth = st.session_state.get("computed_portfolio_value", 0)
    goals_count = len(goals)

    # ── KPI Strip ────────────────────────────────────────────────
    st.markdown(f"""
    <div class='kpi-strip'>
        <div class='kpi-tile'>
            <div class='kpi-label'>💰 Total Wealth</div>
            <div class='kpi-value'>{_fmt_inr(total_wealth) if total_wealth else "—"}</div>
        </div>
        <div class='kpi-tile'>
            <div class='kpi-label'>⚡ Risk Profile</div>
            <div class='kpi-value' style='color:#6366f1;'>{risk_profile}</div>
        </div>
        <div class='kpi-tile'>
            <div class='kpi-label'>🎯 Goals Defined</div>
            <div class='kpi-value'>{goals_count if goals_count else "None yet"}</div>
        </div>
        <div class='kpi-tile'>
            <div class='kpi-label'>📈 Inflation Rate</div>
            <div class='kpi-value'>{inflation_rate*100:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Mid Section: Distribution + Goals ───────────────────────
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>📊 Asset Distribution</div>", unsafe_allow_html=True)

        if imported_df is not None and not imported_df.empty:
            equity_val = imported_df["market_value"].sum() if "market_value" in imported_df.columns else 0
            mf_val = st.session_state.get("mf_total_value", 0)
            fd_val = st.session_state.get("fd_total_value", 0)
            cash_val = st.session_state.get("cash_savings", 0)
            total = equity_val + mf_val + fd_val + cash_val or 1
            distribution = {
                "Equities": round(equity_val / total * 100, 1),
                "Mutual Funds": round(mf_val / total * 100, 1),
                "Fixed Deposits": round(fd_val / total * 100, 1),
                "Cash": round(cash_val / total * 100, 1),
            }
            distribution = {k: v for k, v in distribution.items() if v > 0}
        else:
            distribution = {"Equities": 62, "Mutual Funds": 18, "Fixed Deposits": 12, "Cash": 8}

        fig = _asset_donut(distribution)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("<div class='panel-title'>🎯 Investment Goals Summary</div>", unsafe_allow_html=True)

        if goals:
            tier_colors = {"survival": "#10b981", "safety": "#6366f1", "growth": "#f59e0b"}
            tier_icons  = {"survival": "🟢", "safety": "🔵", "growth": "🟡"}
            for g in goals[:4]:
                tier = g.get("tier", "growth")
                funded = g.get("funded_pct", 0)
                color = tier_colors.get(tier, "#6366f1")
                icon = tier_icons.get(tier, "⚪")
                st.markdown(f"""
                <div class='goal-row'>
                    <div>
                        <div class='goal-label'>{icon} {g.get('name', 'Goal')}</div>
                        <div class='goal-meta'>{g.get('description', '')}</div>
                        <div class='progress-bar' style='background:rgba(255,255,255,0.1); width:100%;'>
                            <div style='width:{funded}%; height:100%;
                                background:{color}; border-radius:999px;'></div>
                        </div>
                    </div>
                    <div style='text-align:right; margin-left:1rem;'>
                        <div class='goal-amount'>{_fmt_inr(g.get("target_value", 0))}</div>
                        <div class='goal-meta' style='color:{color};'>{funded:.0f}% funded</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='text-align:center; padding:2rem 0; color:#64748b;'>
                <div style='font-size:2rem;'>🎯</div>
                <p style='margin:0.5rem 0 0 0;'>No goals defined yet.</p>
                <p style='font-size:0.8rem;'>Start with 'Define My Goals' below.</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Action Routing Cards ─────────────────────────────────────
    st.markdown("<div class='action-section'>", unsafe_allow_html=True)
    st.markdown("<div class='action-title'>What would you like to do today?</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class='action-card card-indigo'>
            <div class='icon'>🧭</div>
            <div class='label'>Define My Goals</div>
            <div class='desc'>Set up your Survival, Safety &amp; Growth investment objectives</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Goal Wizard →", key="btn_define_goals", use_container_width=True):
            logger.info(f"User {user_key} selected path: Define My Goals")
            st.session_state.app_page = "goals_wizard"
            st.rerun()

    with col2:
        st.markdown("""
        <div class='action-card card-teal'>
            <div class='icon'>🔄</div>
            <div class='label'>Review &amp; Update Goals</div>
            <div class='desc'>Revisit and adjust your existing investment objectives</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Goal Review →", key="btn_review_goals", use_container_width=True):
            logger.info(f"User {user_key} selected path: Review & Update Goals")
            st.session_state.app_page = "goals_review"
            st.rerun()

    with col3:
        st.markdown("""
        <div class='action-card card-amber'>
            <div class='icon'>⚡</div>
            <div class='label'>Get Investment Advice</div>
            <div class='desc'>One-time or SIP advice in 2 minutes — no goal setup needed</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Quick Advice →", key="btn_quick_advice", use_container_width=True):
            logger.info(f"User {user_key} selected path: Quick Advice")
            st.session_state.app_page = "quick_advice"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Sign-out ─────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Sign Out", key="btn_signout"):
        logger.info(f"User {user_key} signed out")
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
