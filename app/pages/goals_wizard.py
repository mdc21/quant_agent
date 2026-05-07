"""
YourBestPath — Goal Definition Wizard (5-Step)
Step 1: Monthly Expenses (Survival Floor)
Step 2: Goal Selection Grid (SSG Framework)
Step 3: Per-Goal Configuration with Hidden Math
Step 4: Risk Profile
Step 5: Review & Confirm
"""
import logging
import streamlit as st
import datetime
from core.data.store import DataStore

logger = logging.getLogger(__name__)

GOAL_CATALOG = {
    "survival": [
        {"id": "emergency_fund", "name": "Emergency Fund", "icon": "🏦",
         "desc": "6–12 months of living expenses", "inflation": 0.06},
        {"id": "medical_emergency", "name": "Medical Emergency", "icon": "🏥",
         "desc": "Health contingency corpus", "inflation": 0.12},
        {"id": "job_loss_buffer", "name": "Job Loss Buffer", "icon": "🛡️",
         "desc": "12–24 months income safety net", "inflation": 0.06},
    ],
    "safety": [
        {"id": "retirement", "name": "Retirement", "icon": "🏖️",
         "desc": "25× annual expense rule", "inflation": 0.06},
        {"id": "home_purchase", "name": "Home Purchase", "icon": "🏠",
         "desc": "Down payment + registration", "inflation": 0.08},
        {"id": "children_education", "name": "Children's Education", "icon": "🎓",
         "desc": "10–12% education inflation", "inflation": 0.12},
        {"id": "parent_care", "name": "Parent Care", "icon": "👴",
         "desc": "Elder support & medical expenses", "inflation": 0.10},
        {"id": "debt_freedom", "name": "Debt Freedom", "icon": "⛓️",
         "desc": "Clear all high-interest liabilities", "inflation": 0.0},
    ],
    "growth": [
        {"id": "children_marriage", "name": "Children's Marriage", "icon": "💍",
         "desc": "₹25–50L inflation-adjusted", "inflation": 0.08},
        {"id": "travel", "name": "Travel & Experiences", "icon": "✈️",
         "desc": "Bucket-list travel fund", "inflation": 0.06},
        {"id": "real_estate", "name": "Real Estate", "icon": "🏢",
         "desc": "Second home or commercial property", "inflation": 0.08},
        {"id": "business", "name": "Start a Business", "icon": "🚀",
         "desc": "Seed capital for venture", "inflation": 0.07},
        {"id": "legacy", "name": "Legacy Gift", "icon": "🎁",
         "desc": "Wealth transfer to next generation", "inflation": 0.06},
        {"id": "philanthropy", "name": "Philanthropy", "icon": "🤝",
         "desc": "Charitable giving corpus", "inflation": 0.06},
        {"id": "esg_impact", "name": "ESG Impact", "icon": "🌱",
         "desc": "SEBI-compliant impact investing", "inflation": 0.06},
        {"id": "tax_optimise", "name": "Tax Optimisation", "icon": "📋",
         "desc": "ELSS, 80C, NPS maximisation", "inflation": 0.0},
        {"id": "wealth_creation", "name": "General Wealth", "icon": "📈",
         "desc": "Beat inflation by 4–6% CAGR", "inflation": 0.06},
    ]
}

TIER_COLORS = {"survival": "#f97316", "safety": "#6366f1", "growth": "#10b981"}
TIER_ICONS  = {"survival": "🟠", "safety": "🔵", "growth": "🟢"}


def _fmt_inr(v):
    if v >= 1e7: return f"₹{v/1e7:.2f}Cr"
    if v >= 1e5: return f"₹{v/1e5:.2f}L"
    return f"₹{v:,.0f}"


def render_goals_wizard():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'Inter',sans-serif;}
    .stApp{background:#f8fafc;}
    .step-header{font-size:1.5rem;font-weight:800;color:#1e293b;margin-bottom:0.3rem;}
    .step-sub{color:#64748b;font-size:0.9rem;margin-bottom:1.5rem;}
    .goal-card{
        border:2px solid #e2e8f0;border-radius:14px;padding:1rem;text-align:center;
        cursor:pointer;transition:all 0.2s;background:white;
    }
    .goal-card.selected{border-color:#6366f1;background:rgba(99,102,241,0.08);}
    .goal-card:hover{border-color:#94a3b8;transform:translateY(-2px);}
    .goal-icon{font-size:1.8rem;margin-bottom:0.4rem;}
    .goal-name{font-weight:700;font-size:0.85rem;color:#1e293b;}
    .goal-desc{font-size:0.72rem;color:#94a3b8;margin-top:0.2rem;}
    .insight-box{
        background:rgba(99,102,241,0.08);border-left:4px solid #6366f1;
        border-radius:8px;padding:0.9rem 1.1rem;margin-top:1rem;
        font-size:0.88rem;color:#1e293b;
    }
    .tier-badge{
        display:inline-block;padding:0.3rem 0.8rem;border-radius:20px;
        font-size:0.75rem;font-weight:700;margin-bottom:0.8rem;
    }
    div.stButton>button{
        border-radius:10px!important;font-weight:600!important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Progress bar
    step = st.session_state.get("wizard_step", 1)
    total = 5
    progress = (step - 1) / (total - 1)

    steps_labels = ["💰 Expenses", "🎯 Goals", "⚙️ Configure", "📊 Risk", "✅ Review"]
    cols = st.columns(total)
    for i, (c, label) in enumerate(zip(cols, steps_labels)):
        with c:
            is_done = i + 1 < step
            is_cur  = i + 1 == step
            color = "#6366f1" if is_cur else ("#10b981" if is_done else "#cbd5e1")
            st.markdown(f"""
            <div style='text-align:center;'>
                <div style='width:32px;height:32px;border-radius:50%;background:{color};
                    color:white;font-weight:700;display:flex;align-items:center;
                    justify-content:center;margin:0 auto;font-size:0.85rem;'>
                    {"✓" if is_done else i+1}
                </div>
                <div style='font-size:0.7rem;color:{"#6366f1" if is_cur else "#94a3b8"};
                    margin-top:0.3rem;font-weight:{"700" if is_cur else "400"};'>{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr style='margin:1rem 0;border-color:#e2e8f0;'>", unsafe_allow_html=True)

    # ── STEP 1: Monthly Expenses ─────────────────────────────────
    if step == 1:
        st.markdown("<div class='step-header'>What are your monthly household expenses?</div>", unsafe_allow_html=True)
        st.markdown("<div class='step-sub'>This helps us calculate your Survival Floor — the minimum liquid safety net we protect first.</div>", unsafe_allow_html=True)

        monthly = st.number_input("Monthly Expenses (₹)", min_value=10000, max_value=10000000,
                                  value=st.session_state.get("monthly_expenses", 100000),
                                  step=5000, format="%d")
        floor_12 = monthly * 12
        floor_24 = monthly * 24

        st.markdown(f"""
        <div class='insight-box'>
            <b>🛡️ Your Survival Floor:</b><br>
            • 12-month floor: <b>{_fmt_inr(floor_12)}</b> — minimum emergency fund<br>
            • 24-month buffer: <b>{_fmt_inr(floor_24)}</b> — recommended for self-employed<br>
            <br>
            <i>We will prioritise funding this before allocating to Growth goals.</i>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Next: Select Goals →", key="step1_next", use_container_width=True):
            logger.info(f"Goal Wizard Step 1: Monthly expenses set to {monthly}")
            st.session_state.monthly_expenses = monthly
            st.session_state.survival_floor = floor_12
            st.session_state.wizard_step = 2
            st.rerun()

    # ── STEP 2: Goal Selection Grid ──────────────────────────────
    elif step == 2:
        st.markdown("<div class='step-header'>Select Your Investment Goals</div>", unsafe_allow_html=True)
        st.markdown("<div class='step-sub'>Choose all that apply — you can always update these later.</div>", unsafe_allow_html=True)

        if "selected_goals" not in st.session_state:
            st.session_state.selected_goals = set()

        for tier, goals in GOAL_CATALOG.items():
            color = TIER_COLORS[tier]
            icon = TIER_ICONS[tier]
            st.markdown(f"""
            <div class='tier-badge' style='background:{color}20;color:{color};'>
                {icon} {tier.upper()}
            </div>
            """, unsafe_allow_html=True)

            n_cols = min(len(goals), 4) if tier != "growth" else 5
            cols = st.columns(n_cols)
            for i, g in enumerate(goals):
                with cols[i % n_cols]:
                    selected = g["id"] in st.session_state.selected_goals
                    border = color if selected else "#e2e8f0"
                    bg = f"{color}15" if selected else "white"
                    check = "✅ " if selected else ""
                    st.markdown(f"""
                    <div class='goal-card' style='border-color:{border};background:{bg};'>
                        <div class='goal-icon'>{g["icon"]}</div>
                        <div class='goal-name'>{check}{g["name"]}</div>
                        <div class='goal-desc'>{g["desc"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Select" if not selected else "Deselect",
                                 key=f"goal_{g['id']}", use_container_width=True):
                        if selected:
                            st.session_state.selected_goals.discard(g["id"])
                        else:
                            st.session_state.selected_goals.add(g["id"])
                        st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back", key="step2_back"):
                st.session_state.wizard_step = 1; st.rerun()
        with col_next:
            if st.button(f"Next: Configure {len(st.session_state.selected_goals)} Goals →",
                         key="step2_next", use_container_width=True):
                if not st.session_state.selected_goals:
                    st.warning("Please select at least one goal.")
                else:
                    logger.info(f"Goal Wizard Step 2: Selected {len(st.session_state.selected_goals)} goals")
                    st.session_state.wizard_step = 3; st.rerun()

    # ── STEP 3: Configure Each Goal ──────────────────────────────
    elif step == 3:
        st.markdown("<div class='step-header'>Configure Your Goals</div>", unsafe_allow_html=True)
        st.markdown("<div class='step-sub'>Set your targets — we'll show the inflation-adjusted future value.</div>", unsafe_allow_html=True)

        inflation_rate = st.session_state.get("inflation_rate", 0.06)
        if "goal_configs" not in st.session_state:
            st.session_state.goal_configs = {}

        # Flatten catalog
        all_goals = {g["id"]: {**g, "tier": tier}
                     for tier, gs in GOAL_CATALOG.items() for g in gs}

        for gid in st.session_state.selected_goals:
            g = all_goals.get(gid, {})
            if not g:
                continue
            tier = g.get("tier", "growth")
            color = TIER_COLORS[tier]

            with st.expander(f"{g['icon']} {g['name']}", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    target = st.number_input(
                        f"Target Amount (₹)",
                        min_value=0, value=st.session_state.goal_configs.get(gid, {}).get("target", 1000000),
                        step=100000, format="%d", key=f"cfg_amt_{gid}"
                    )
                with col_b:
                    horizon = st.slider(
                        "Time Horizon (Years)", 1, 40,
                        value=st.session_state.goal_configs.get(gid, {}).get("horizon", 10),
                        key=f"cfg_horizon_{gid}"
                    )

                infl = g.get("inflation", inflation_rate)
                fv = target * ((1 + infl) ** horizon)
                st.markdown(f"""
                <div class='insight-box' style='border-color:{color};'>
                    At <b>{infl*100:.0f}% inflation</b>, your {_fmt_inr(target)} target
                    requires <b>{_fmt_inr(fv)}</b> in {horizon} years.
                </div>
                """, unsafe_allow_html=True)

                st.session_state.goal_configs[gid] = {
                    "id": gid, "name": g["name"], "tier": tier,
                    "icon": g["icon"], "target": target,
                    "horizon": horizon, "future_value": fv,
                    "target_value": fv, "funded_pct": 0,
                    "description": g["desc"]
                }

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back", key="step3_back"):
                st.session_state.wizard_step = 2; st.rerun()
        with col_next:
            if st.button("Next: Set Risk Profile →", key="step3_next", use_container_width=True):
                logger.info("Goal Wizard Step 3: Configured goal targets and horizons")
                st.session_state.wizard_step = 4; st.rerun()

    # ── STEP 4: Risk Profile ─────────────────────────────────────
    elif step == 4:
        st.markdown("<div class='step-header'>What is your risk appetite?</div>", unsafe_allow_html=True)
        st.markdown("<div class='step-sub'>This determines how we distribute your capital across equities, debt, and passive instruments.</div>", unsafe_allow_html=True)

        profiles = [
            {"id": "Conservative", "icon": "🛡️", "color": "#10b981",
             "label": "Conservative",
             "desc": "Capital protection first. Lower returns, stable growth. Suited for short horizons or low risk tolerance.",
             "alloc": "Debt 60% | Equity 25% | Cash 15%"},
            {"id": "Moderate", "icon": "⚖️", "color": "#6366f1",
             "label": "Moderate",
             "desc": "Balanced growth with managed risk. Mid-term goals, comfortable with some market swings.",
             "alloc": "Equity 50% | Debt 35% | Cash 15%"},
            {"id": "Aggressive", "icon": "🚀", "color": "#f59e0b",
             "label": "Aggressive",
             "desc": "Maximum growth potential. Significant equity exposure. For long-term wealth creation with high risk tolerance.",
             "alloc": "Equity 80% | Passive 15% | Debt 5%"},
        ]

        current_risk = st.session_state.get("user_risk_profile", "Moderate")
        cols = st.columns(3)
        for i, p in enumerate(profiles):
            with cols[i]:
                selected = current_risk == p["id"]
                border = p["color"] if selected else "#e2e8f0"
                bg = f"{p['color']}12" if selected else "white"
                st.markdown(f"""
                <div style='border:2px solid {border};border-radius:14px;padding:1.2rem;
                    background:{bg};text-align:center;min-height:200px;'>
                    <div style='font-size:2rem;'>{p["icon"]}</div>
                    <div style='font-weight:800;font-size:1rem;color:{p["color"]};margin:0.5rem 0;'>{p["label"]}</div>
                    <div style='font-size:0.78rem;color:#64748b;margin-bottom:0.8rem;'>{p["desc"]}</div>
                    <div style='background:{p["color"]}20;border-radius:8px;padding:0.4rem;
                        font-size:0.72rem;font-weight:600;color:{p["color"]};'>{p["alloc"]}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"{'✓ Selected' if selected else 'Select'} {p['label']}",
                             key=f"risk_{p['id']}", use_container_width=True):
                    st.session_state.user_risk_profile = p["id"]
                    st.rerun()

        col_back, col_next = st.columns([1, 3])
        with col_back:
            if st.button("← Back", key="step4_back"):
                st.session_state.wizard_step = 3; st.rerun()
        with col_next:
            if st.button("Next: Review Summary →", key="step4_next", use_container_width=True):
                logger.info(f"Goal Wizard Step 4: Risk profile set to {st.session_state.get('user_risk_profile')}")
                st.session_state.wizard_step = 5; st.rerun()

    # ── STEP 5: Review & Save ────────────────────────────────────
    elif step == 5:
        st.markdown("<div class='step-header'>Review Your Financial Plan</div>", unsafe_allow_html=True)
        st.markdown("<div class='step-sub'>Confirm your goals and risk profile before we generate your fiduciary portfolio.</div>", unsafe_allow_html=True)

        risk = st.session_state.get("user_risk_profile", "Moderate")
        configs = st.session_state.get("goal_configs", {})
        monthly = st.session_state.get("monthly_expenses", 0)

        st.markdown(f"""
        <div style='background:rgba(99,102,241,0.06);border-radius:12px;padding:1rem 1.2rem;margin-bottom:1rem;'>
            <b>Risk Profile:</b> {risk} &nbsp;|&nbsp;
            <b>Monthly Expenses:</b> {_fmt_inr(monthly)} &nbsp;|&nbsp;
            <b>Goals Selected:</b> {len(configs)}
        </div>
        """, unsafe_allow_html=True)

        for tier_name, tier_goals in [
            ("🟠 Survival", [g for g in configs.values() if g.get("tier") == "survival"]),
            ("🔵 Safety",   [g for g in configs.values() if g.get("tier") == "safety"]),
            ("🟢 Growth",   [g for g in configs.values() if g.get("tier") == "growth"]),
        ]:
            if not tier_goals:
                continue
            st.markdown(f"**{tier_name}**")
            for g in tier_goals:
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.markdown(f"{g['icon']} **{g['name']}**")
                with col2:
                    st.markdown(f"Target: {_fmt_inr(g['target'])}")
                with col3:
                    st.markdown(f"In {g['horizon']} yrs → {_fmt_inr(g['future_value'])}")

        col_back, col_save = st.columns([1, 3])
        with col_back:
            if st.button("← Back", key="step5_back"):
                st.session_state.wizard_step = 4; st.rerun()
        with col_save:
            if st.button("✅ Save Goals & Open Dashboard →", key="step5_save", use_container_width=True):
                logger.info("Goal Wizard Step 5: Committing goals to DataStore")
                with st.spinner("Saving your goals securely..."):
                    try:
                        ds = DataStore()
                        user_key = st.session_state.get("user_key", "user_1")
                        goals_list = list(configs.values())
                        ds.save_goals(
                            user_key, goals_list,
                            risk_tolerance=risk,
                            inflation_rate=st.session_state.get("inflation_rate", 0.06)
                        )
                        logger.info("Goal Wizard Step 5: Save successful. Routing to dashboard.")
                        st.session_state.onboarding_complete = True
                        st.session_state.app_page = "dashboard"
                        st.session_state.wizard_step = 1
                        st.success("✅ Goals saved! Opening your fiduciary dashboard...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save goals: {e}")
