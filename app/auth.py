"""
YourBestPath Authentication Page
Login & Registration UI — gating the entire fiduciary engine.
"""
import logging
import streamlit as st
from core.auth.user_store import UserStore

logger = logging.getLogger(__name__)

def _inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* 50/50 Split Background */
    .stApp { 
        background: linear-gradient(90deg, #040d21 0%, #0a1930 50%, #f8fafc 50%, #f8fafc 100%) !important; 
    }
    
    /* Hide the sidebar completely */
    section[data-testid="stSidebar"] { display: none !important; width: 0 !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    
    /* Remove default main padding to allow split screen */
    .stApp > header { display: none !important; }
    .block-container { padding-top: 2rem !important; max-width: 1200px !important; }
    
    /* Target the login card column */
    div[data-testid="stColumn"]:has(.login-marker),
    div[data-testid="column"]:has(.login-marker),
    div[data-testid="stVerticalBlock"]:has(.login-marker) {
        background: #ffffff !important;
        border-radius: 16px !important;
        padding: 2.5rem 2rem !important;
        box-shadow: 0 15px 50px rgba(0,0,0,0.06) !important;
        border: 1px solid #f1f5f9 !important;
        margin-top: 6rem !important;
        margin-left: 2rem !important;
    }
    
    /* Streamlit tabs flat styling */
    div[data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 2px solid #e2e8f0 !important;
        justify-content: space-around !important;
        margin-bottom: 1.5rem !important;
    }
    div[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: #64748b !important;
        padding-bottom: 0.8rem !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        color: #0f172a !important;
        border-bottom: 3px solid #0f172a !important;
    }
    
    .security-badge {
        text-align:center;
        font-size:0.75rem;
        color:#64748b;
        margin-top:1.5rem;
        display:flex;
        align-items:center;
        justify-content:center;
        gap:0.4rem;
    }
    
    /* Input Styling */
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        padding: 0.6rem 0.8rem !important;
        font-size: 0.95rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #0f172a !important;
        box-shadow: 0 0 0 2px rgba(15,23,42,0.1) !important;
    }
    
    /* Button Styling */
    div.stButton > button {
        background: #09101f !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 1rem !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        width: 100% !important;
        margin-top: 1rem !important;
    }
    div.stButton > button:hover {
        background: #1e293b !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_auth_page() -> bool:
    """
    Renders the Login/Register page matching the 50/50 split UI.
    """
    _inject_css()

    if st.session_state.get("authenticated"):
        return True

    # Use a 2-column layout for the 50/50 split screen
    col_left, col_right = st.columns(2, gap="large")

    # ── LEFT COLUMN (BRANDING) ──────────────────────────────────────────────
    with col_left:
        st.markdown("""
<div style="height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; padding-top: 4rem;">
    <!-- Glowing Rings Visual -->
    <div style="position: relative; width: 300px; height: 300px; margin-bottom: 3rem;">
        <!-- Outer Green Ring -->
        <div style="position: absolute; inset: 0; border-radius: 50%; border: 4px solid #10b981; 
             box-shadow: 0 0 40px rgba(16, 185, 129, 0.6), inset 0 0 30px rgba(16, 185, 129, 0.4);"></div>
        <!-- Middle Blue Ring -->
        <div style="position: absolute; inset: 40px; border-radius: 50%; border: 4px solid #3b82f6; 
             box-shadow: 0 0 40px rgba(59, 130, 246, 0.6), inset 0 0 20px rgba(59, 130, 246, 0.4);"></div>
        <!-- Inner Gold Ring -->
        <div style="position: absolute; inset: 80px; border-radius: 50%; border: 4px solid #fbbf24; 
             box-shadow: 0 0 50px rgba(251, 191, 36, 0.8), inset 0 0 20px rgba(251, 191, 36, 0.6);"></div>
        <!-- Core Glow -->
        <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); 
             width: 80px; height: 80px; background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, transparent 70%);"></div>
    </div>
    <!-- Brand Typography -->
    <div style="text-align: center; margin-top: 2rem;">
        <h1 style="font-family: 'Playfair Display', serif; font-size: 3.5rem; font-weight: 700; color: #ffffff; margin: 0; letter-spacing: -0.5px;">YourBestPath</h1>
        <p style="font-family: 'Inter', sans-serif; font-size: 1.25rem; font-weight: 400; color: #d1d5db; margin-top: 0.5rem;">Your North Star for Building Wealth</p>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── RIGHT COLUMN (AUTH CARD) ────────────────────────────────────────────
    with col_right:
        st.markdown("<div class='login-marker'></div>", unsafe_allow_html=True)
        tab_sign_in, tab_register = st.tabs(["Sign In", "Create Account"])

        store = UserStore()

        with tab_sign_in:
            st.markdown("<br>", unsafe_allow_html=True)
            email = st.text_input("Email Address", placeholder="", key="login_email")
            password = st.text_input("Password", type="password", placeholder="", key="login_pass")
            
            if st.button("Continue", key="btn_login"):
                logger.info(f"Login attempt for email: {email}")
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    with st.spinner("Verifying..."):
                        result = store.authenticate(email, password)
                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.session_state.authenticated = True
                        st.session_state.user_key = result["user_key"]
                        st.session_state.user_name = result["name"]
                        st.session_state.user_role = result["role"]
                        st.session_state.user_risk_profile = result.get("risk_profile", "Moderate")
                        st.session_state.onboarding_complete = result.get("onboarding_complete", False)
                        st.rerun()

            st.markdown("""
            <div class='security-badge'>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg>
                Secured by 256-bit AES Encryption
            </div>
            """, unsafe_allow_html=True)

        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            r_name = st.text_input("Full Name", placeholder="", key="reg_name")
            r_email = st.text_input("Email Address", placeholder="", key="reg_email")
            r_pass = st.text_input("Create Password", type="password", placeholder="", key="reg_pass")
            r_pass2 = st.text_input("Confirm Password", type="password", placeholder="", key="reg_pass2")

            if st.button("Create Account", key="btn_register"):
                if not all([r_name, r_email, r_pass, r_pass2]):
                    st.error("Please fill in all fields.")
                elif r_pass != r_pass2:
                    st.error("Passwords do not match.")
                elif len(r_pass) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    with st.spinner("Creating your account..."):
                        result = store.register(r_name, r_email, r_pass)
                    if "error" in result:
                        st.error(f"❌ {result['error']}")
                    else:
                        st.success("✅ Account created! Please sign in.")

    return False
