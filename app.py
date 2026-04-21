import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import re
from chatbot_backend import chatbot, get_user_profile

# CONFIG
st.set_page_config(
    page_title="MoneyBOT",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# SESSION STATE
def _init_state():
    defaults = {
        "current_page": "BOT",
        "user_step":    1,
        "messages":     [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# GLOBAL CSS  — dark finance theme, matching the wireframe's dark palette
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Force dark everywhere — overrides Streamlit's light defaults ── */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #0e1a14 !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background-color: #0e1a14 !important;
    border-bottom: 1px solid #2d4a35 !important;
}
table { background: #1c2d21 !important; }
th    { background: #162318 !important; color: #3ddc84 !important;
        border-color: #2d4a35 !important; }
td    { border-color: #2d4a35 !important; color: #e8f5ec !important; }
[data-testid="stExpander"] {
    background: #1c2d21 !important;
    border: 1px solid #2d4a35 !important; border-radius: 10px !important;
}
[data-testid="stMetric"] {
    background: #1c2d21 !important; border: 1px solid #2d4a35 !important;
    border-radius: 10px !important; padding: 0.75rem 1rem !important;
}
[data-testid="stMetricLabel"] { color: #9dbda8 !important; }
[data-testid="stMetricValue"] { color: #3ddc84 !important; font-family: 'Space Mono',monospace !important; }

/* ── Root palette ── */
:root {
    --bg:        #0e1a14;
    --surface:   #162318;
    --card:      #1c2d21;
    --border:    #2d4a35;
    --accent:    #3ddc84;
    --accent2:   #27ae60;
    --muted:     #5a8a68;
    --text:      #e8f5ec;
    --subtext:   #9dbda8;
    --danger:    #e74c3c;
    --warn:      #f39c12;
    --mono:      'Space Mono', monospace;
    --sans:      'DM Sans', sans-serif;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: var(--sans) !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}
.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem;
    max-width: 1100px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Sidebar buttons ── */
[data-testid="stSidebar"] .stButton button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--subtext) !important;
    border-radius: 8px !important;
    font-family: var(--sans) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 0.5rem 0.9rem !important;
    transition: all 0.15s ease !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: var(--card) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}
[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #0e1a14 !important;
    font-weight: 700 !important;
}

/* ── Page headings ── */
h1 { font-family: var(--mono) !important; color: var(--accent) !important;
     font-size: 1.6rem !important; letter-spacing: -0.5px !important; }
h2 { font-family: var(--mono) !important; color: var(--text) !important;
     font-size: 1.1rem !important; }
h3 { font-family: var(--sans) !important; color: var(--subtext) !important;
     font-size: 0.95rem !important; font-weight: 600 !important; }

/* ── Metric cards ── */
.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
}
.metric-label {
    font-size: 0.72rem;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: var(--mono);
    margin-bottom: 4px;
}
.metric-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--accent);
    font-family: var(--mono);
    line-height: 1;
}
.metric-sub {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 3px;
}

/* ── Stat bar ── */
.stat-bar-bg {
    background: var(--border);
    border-radius: 99px;
    height: 6px;
    margin-top: 8px;
    overflow: hidden;
}
.stat-bar-fill {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, var(--accent2), var(--accent));
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}
[data-testid="stChatInput"] textarea {
    background: var(--card) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: var(--sans) !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(61,220,132,0.15) !important;
}

/* ── Inputs / select ── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
.stTextArea textarea {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: var(--sans) !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(61,220,132,0.15) !important;
}
label { color: var(--subtext) !important; font-size: 0.83rem !important;
        font-weight: 500 !important; }

/* ── Primary button ── */
.stButton button[kind="primary"] {
    background: var(--accent) !important;
    color: #0e1a14 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: var(--sans) !important;
}
.stButton button {
    border: 1px solid var(--border) !important;
    background: transparent !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: var(--sans) !important;
}

/* ── Progress bar ── */
.stProgress > div > div {
    background: var(--accent) !important;
}
.stProgress > div {
    background: var(--border) !important;
}

/* ── Success / info / warning banners ── */
.stSuccess {
    background: rgba(61,220,132,0.1) !important;
    border: 1px solid var(--accent2) !important;
    border-radius: 8px !important;
    color: var(--accent) !important;
}
.stWarning {
    background: rgba(243,156,18,0.1) !important;
    border: 1px solid var(--warn) !important;
    border-radius: 8px !important;
}
.stInfo {
    background: rgba(61,220,132,0.07) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Tab styling — evenly distributed ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--card) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 3px !important;
    display: flex !important;
    width: 100% !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--subtext) !important;
    border-radius: 6px !important;
    font-family: var(--sans) !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    flex: 1 !important;
    text-align: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: #0e1a14 !important;
    font-weight: 700 !important;
}

/* ── Plotly chart backgrounds ── */
.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
</style>
""", unsafe_allow_html=True)

# HELPER CONSTANTS & UI
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9dbda8", family="DM Sans"),
    margin=dict(l=20, r=20, t=40, b=20),
)

def metric_card(label: str, value: str, sub: str = "", bar_pct: int = 0):
    bar_html = ""
    if bar_pct > 0:
        pct = min(bar_pct, 100)
        bar_html = f"""
        <div class="stat-bar-bg">
            <div class="stat-bar-fill" style="width:{pct}%"></div>
        </div>"""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {'<div class="metric-sub">' + sub + '</div>' if sub else ''}
        {bar_html}
    </div>""", unsafe_allow_html=True)

# SIDEBAR
def render_sidebar():
    p = get_user_profile()

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0 0.5rem 0;'>
            <div style='font-family:"Space Mono",monospace; font-size:1.3rem;
                        color:#3ddc84; font-weight:700; letter-spacing:-1px;'>
                💰 MoneyBOT
            </div>
            <div style='font-size:0.7rem; color:#5a8a68; margin-top:2px;
                        font-family:"DM Sans",sans-serif;'>
                AI Financial Advisor
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Profile mini-card in sidebar
        if p.get("name"):
            savings_pct = int(p["savings_rate"] * 100)
            color = "#3ddc84" if savings_pct >= 20 else "#f39c12" if savings_pct >= 10 else "#e74c3c"
            st.markdown(f"""
            <div style='background:#1c2d21; border:1px solid #2d4a35;
                        border-radius:10px; padding:0.75rem 1rem; margin:0.5rem 0;'>
                <div style='font-size:0.72rem; color:#9dbda8; text-transform:uppercase;
                            letter-spacing:1px; font-family:"Space Mono",monospace;'>
                    {p['name']}
                </div>
                <div style='font-size:1.1rem; color:#3ddc84; font-weight:700;
                            font-family:"Space Mono",monospace; margin-top:2px;'>
                    ₹{p["income"]:,.0f}
                    <span style='font-size:0.7rem; color:#5a8a68;'>/mo</span>
                </div>
                <div style='font-size:0.75rem; color:{color}; margin-top:3px;'>
                    Saving {savings_pct}% of income
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background:#1c2d21; border:1px dashed #2d4a35;
                        border-radius:10px; padding:0.6rem 1rem; margin:0.5rem 0;
                        font-size:0.78rem; color:#5a8a68; text-align:center;'>
                ⚙️ Set up your profile first
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        pages = [
            ("🏠", "About Project"),
            ("🤖", "BOT"),
            ("📊", "Visualization"),
            ("📈", "Model Evaluation"),
            ("🎯", "Goal Tracking"),
            ("📰", "News"),
        ]

        for icon, page in pages:
            is_active = st.session_state.current_page == page
            btn_type  = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {page}", use_container_width=True,
                         type=btn_type, key=f"nav_{page}"):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        # User button at bottom
        if st.button("👤  USER", use_container_width=True,
                     type="primary" if st.session_state.current_page == "USER"
                     else "secondary", key="nav_USER"):
            st.session_state.current_page = "USER"
            st.rerun()

        st.markdown("""
        <div style='font-size:0.65rem; color:#2d4a35; text-align:center;
                    margin-top:1rem; font-family:"Space Mono",monospace;'>
            v1.0 · NLP + Rule Engine
        </div>
        """, unsafe_allow_html=True)

# PAGE: ABOUT
def page_about():
    st.markdown("# 📘 About MoneyBOT")
    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2], gap="large")

    with col1:
        # Feature pills
        st.markdown("""
        <div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:1.5rem">
            <span style="background:#1c2d21; border:1px solid #3ddc84; color:#3ddc84;
                         padding:4px 12px; border-radius:99px; font-size:0.78rem;
                         font-family:'DM Sans',sans-serif; font-weight:600">
                🤖 DistilBERT NLP
            </span>
            <span style="background:#1c2d21; border:1px solid #27ae60; color:#27ae60;
                         padding:4px 12px; border-radius:99px; font-size:0.78rem;
                         font-family:'DM Sans',sans-serif; font-weight:600">
                📊 Rule-Based Engine
            </span>
            <span style="background:#1c2d21; border:1px solid #5a8a68; color:#9dbda8;
                         padding:4px 12px; border-radius:99px; font-size:0.78rem;
                         font-family:'DM Sans',sans-serif; font-weight:600">
                ⚡ Streamlit
            </span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="color:#e8f5ec; font-size:0.92rem; line-height:1.7; margin-bottom:1.2rem">
            <strong style="color:#3ddc84">MoneyBOT</strong> is an AI-powered personal finance
            advisor that understands natural language, tracks your spending, and gives
            personalised investment advice — all without storing your data anywhere.
        </p>
        """, unsafe_allow_html=True)

        # How it works — styled steps
        steps = [
            ("01", "Set up your profile", "Add your income, age, and monthly expenses via the USER page"),
            ("02", "Chat naturally", "Ask the bot anything — track spending, check balance, analyse trends"),
            ("03", "Get investment advice", "The rule engine personalises a portfolio based on your profile"),
            ("04", "Track your goals", "Set savings targets and monitor progress on the Goal Tracking page"),
        ]
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#5a8a68;
                    text-transform:uppercase; letter-spacing:1.5px; margin-bottom:0.8rem">
            How it works
        </div>
        """, unsafe_allow_html=True)
        for num, title, desc in steps:
            st.markdown(f"""
            <div style="display:flex; gap:14px; margin-bottom:0.9rem; align-items:flex-start">
                <div style="background:#3ddc84; color:#0e1a14; font-family:'Space Mono',monospace;
                             font-weight:700; font-size:0.7rem; padding:4px 8px; border-radius:6px;
                             flex-shrink:0; margin-top:2px; min-width:28px; text-align:center">
                    {num}
                </div>
                <div>
                    <div style="color:#e8f5ec; font-weight:600; font-size:0.88rem;
                                 font-family:'DM Sans',sans-serif">{title}</div>
                    <div style="color:#9dbda8; font-size:0.8rem; margin-top:2px;
                                 font-family:'DM Sans',sans-serif; line-height:1.5">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# Architecture table — styled
st.markdown("""
<div style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#5a8a68;
            text-transform:uppercase; letter-spacing:1.5px; margin:1.2rem 0 0.8rem 0">
    Architecture
</div>
<div style="background:#1c2d21; border:1px solid #2d4a35; border-radius:10px;
            overflow:hidden; margin-bottom:1.2rem">
    <table style="width:100%; border-collapse:collapse">
        <thead>
            <tr style="background:#162318">
                <th style="padding:10px 14px; text-align:left; color:#3ddc84;
                           font-family:'Space Mono',monospace; font-size:0.72rem;
                           font-weight:700; letter-spacing:1px; text-transform:uppercase;
                           border-bottom:1px solid #2d4a35">Layer</th>
                <th style="padding:10px 14px; text-align:left; color:#3ddc84;
                           font-family:'Space Mono',monospace; font-size:0.72rem;
                           font-weight:700; letter-spacing:1px; text-transform:uppercase;
                           border-bottom:1px solid #2d4a35">Technology</th>
            </tr>
        </thead>
        <tbody>
            <tr style="border-bottom:1px solid #2d4a35">
                <td style="padding:9px 14px; color:#9dbda8; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">NLP Intent Detection</td>
                <td style="padding:9px 14px; color:#e8f5ec; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">DistilBERT — 1,578 patterns / 13 classes</td>
            </tr>
            <tr style="border-bottom:1px solid #2d4a35">
                <td style="padding:9px 14px; color:#9dbda8; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Financial Processing Engine</td>
                <td style="padding:9px 14px; color:#e8f5ec; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Rule-Based Logic (expenses, savings, goals)</td>
            </tr>
            <tr style="border-bottom:1px solid #2d4a35">
                <td style="padding:9px 14px; color:#9dbda8; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Investment Recommendation Engine</td>
                <td style="padding:9px 14px; color:#e8f5ec; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Rule-Based Expert System (7 rules + 2 safety gates)</td>
            </tr>
            <tr style="border-bottom:1px solid #2d4a35">
                <td style="padding:9px 14px; color:#9dbda8; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">State Management</td>
                <td style="padding:9px 14px; color:#e8f5ec; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Streamlit Session State</td>
            </tr>
            <tr>
                <td style="padding:9px 14px; color:#9dbda8; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">User Interface</td>
                <td style="padding:9px 14px; color:#e8f5ec; font-size:0.82rem;
                           font-family:'DM Sans',sans-serif">Streamlit</td>
            </tr>
        </tbody>
    </table>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card" style="margin-bottom:0.8rem">
            <div class="metric-label">NLP Model</div>
            <div class="metric-value" style="font-size:1rem">DistilBERT</div>
            <div class="metric-sub">13 intent classes · 1,578 patterns</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-card" style="margin-bottom:0.8rem">
            <div class="metric-label">Investment Engine</div>
            <div class="metric-value" style="font-size:1rem">Rule-Based</div>
            <div class="metric-sub">7 rules · 2 safety gates · 5 instruments</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Why not ML for investment?</div>
            <div class="metric-value" style="font-size:1rem; color:#f39c12">24%</div>
            <div class="metric-sub">ML accuracy on Finance_Trends.csv<br>
            (= random guessing — dataset labels had zero correlation with features)</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Chatbot capabilities
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#5a8a68;
                text-transform:uppercase; letter-spacing:1.5px; margin-bottom:1rem">
        What the Chatbot Can Do
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("💸", "Track Income",
         "Add any income source",
         ["salary credited 40k", "bonus received 5000", "earned 1.5 lakh"]),
        ("📤", "Track Expenses",
         "Log spending by category",
         ["spent 500 on food", "paid 1200 for rent", "bought shoes for 2k"]),
        ("💰", "Check Balance",
         "See savings & spending at a glance",
         ["what is my balance", "how much have I saved", "show my savings"]),
        ("📊", "Monthly Analysis",
         "Full income vs expense breakdown",
         ["show monthly report", "how much did I spend", "monthly analysis"]),
        ("📂", "Category Breakdown",
         "See where your money goes",
         ["show category breakdown", "what did I spend on food"]),
        ("📈", "Investment Advice",
         "Personalised portfolio based on your profile",
         ["where should I invest", "give investment advice", "where do I put my money"]),
        ("⚖️", "Risk Assessment",
         "Understand your risk profile",
         ["what is my risk profile", "am I a high risk investor"]),
        ("✂️", "Save More Advice",
         "Specific cuts from your real spending data",
         ["how can I save more", "reduce my expenses", "help me cut spending"]),
        ("🎯", "Goal Planning",
         "Set targets and track progress",
         ["I want to save for a bike", "how long to save 1 lakh"]),
        ("➕", "Add to Goals",
         "Contribute to a goal through chat",
         ["add 5k to bike goal", "put 2000 towards trip", "add 1 lakh towards bike"]),
    ]

    cols = st.columns(5)
    for i, (icon, title, desc, examples) in enumerate(features):
        with cols[i % 5]:
            eg_html = "<br>".join(
                f'<span style="background:#162318; color:#3ddc84; padding:2px 7px; '
                f'border-radius:4px; font-size:0.68rem; font-family:\'Space Mono\',monospace; '
                f'border:1px solid #2d4a35; white-space:nowrap">{e}</span>'
                for e in examples[:2]
            )
            st.markdown(f"""
            <div style="background:#1c2d21; border:1px solid #2d4a35;
                         border-top:3px solid #3ddc84; border-radius:8px;
                         padding:12px 12px 10px 12px; margin-bottom:10px;
                         height:100%">
                <div style="font-size:1.2rem; margin-bottom:5px">{icon}</div>
                <div style="font-family:'DM Sans',sans-serif; font-weight:700;
                             color:#e8f5ec; font-size:0.86rem;
                             margin-bottom:4px">{title}</div>
                <div style="font-size:0.75rem; color:#9dbda8; margin-bottom:8px;
                             font-family:'DM Sans',sans-serif;
                             line-height:1.4">{desc}</div>
                <div style="display:flex; flex-direction:column; gap:4px">{eg_html}</div>
            </div>
            """, unsafe_allow_html=True)

# PAGE: USER SETUP
def page_user():
    st.markdown("# 👤 User Setup")
    st.markdown("<hr>", unsafe_allow_html=True)

    p = get_user_profile()
    step = st.session_state.user_step

    # Progress bar
    st.progress((step - 1) / 3, text=f"Step {step} of 4")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step content 
    if step == 1:
        st.markdown("### 👋 Basic Info")
        name = st.text_input("Your name", value=p.get("name", ""),
                             placeholder="e.g. Surip")
        age  = st.number_input("Age", min_value=18, max_value=80,
                               value=int(p.get("age", 25)), step=1)
        # Write back immediately
        st.session_state.user_profile["name"] = name
        st.session_state.user_profile["age"]  = age

    elif step == 2:
        st.markdown("### 💼 Monthly Income")
        income = st.number_input(
            "Monthly take-home income (₹)",
            min_value=0, max_value=10_000_000,
            value=int(p.get("income", 0)), step=1000,
            format="%d",
            help="Enter your net monthly salary / total monthly income"
        )
        st.session_state.user_profile["income"] = income

        if income > 0:
            st.info(f"Annual income: **₹{income * 12:,.0f}**")

    elif step == 3:
        st.markdown("### 📤 Monthly Expenses")
        col1, col2 = st.columns(2)
        with col1:
            necessary = st.number_input(
                "Necessary expenses (₹)",
                min_value=0, max_value=10_000_000,
                value=int(p.get("necessary", 0)), step=500, format="%d",
                help="Rent, groceries, bills, commute"
            )
        with col2:
            leisure = st.number_input(
                "Leisure expenses (₹)",
                min_value=0, max_value=10_000_000,
                value=int(p.get("leisure", 0)), step=500, format="%d",
                help="Eating out, entertainment, shopping"
            )
        st.session_state.user_profile["necessary"] = necessary
        st.session_state.user_profile["leisure"]   = leisure

        inc = p.get("income", 0)
        total_exp = necessary + leisure
        if inc > 0 and total_exp > 0:
            savings = inc - total_exp
            sr_pct  = savings / inc * 100
            color   = "normal" if sr_pct >= 20 else "inverse"
            st.markdown("**Quick preview:**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Income",   f"₹{inc:,.0f}")
            c2.metric("Expenses", f"₹{total_exp:,.0f}")
            c3.metric("Savings",  f"₹{savings:,.0f}", f"{sr_pct:.1f}%",
                      delta_color=color)

    elif step == 4:
        st.markdown("### ✅ Confirm Profile")

        inc         = p.get("income", 0)
        necessary   = p.get("necessary", 0)
        leisure     = p.get("leisure", 0)
        total_exp   = necessary + leisure
        savings     = inc - total_exp
        sr          = savings / inc if inc else 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Name</div>
                <div class="metric-value" style="font-size:1.1rem">
                    {p.get('name', '—')}
                </div>
                <div class="metric-sub">Age {p.get('age', '—')}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            sr_color = "#3ddc84" if sr >= 0.20 else "#f39c12" if sr >= 0.10 else "#e74c3c"
            sr_label = "Healthy ✅" if sr >= 0.20 else "Low ⚠️" if sr >= 0.10 else "Critical ❌"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Savings Rate</div>
                <div class="metric-value" style="color:{sr_color}">
                    {sr*100:.1f}%
                </div>
                <div class="metric-sub">{sr_label}</div>
                <div class="stat-bar-bg">
                    <div class="stat-bar-fill"
                         style="width:{min(int(sr*100),100)}%;
                                background:{'linear-gradient(90deg,#27ae60,#3ddc84)' if sr>=0.2
                                            else 'linear-gradient(90deg,#e67e22,#f39c12)'}">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Income",      f"₹{inc:,.0f}")
        c2.metric("Necessary",   f"₹{necessary:,.0f}")
        c3.metric("Leisure",     f"₹{leisure:,.0f}")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("💾  Save Profile", type="primary", use_container_width=True):
            st.session_state.user_profile.update({
                "monthly_spent": total_exp,
                "savings":       savings,
                "savings_rate":  sr,
            })
            st.success("✅ Profile saved! Head to the **BOT** page to start chatting.")
            st.balloons()

    # Navigation buttons
    st.markdown("<br>", unsafe_allow_html=True)
    col_back, col_fwd = st.columns(2)

    with col_back:
        if step > 1:
            if st.button("⬅  Back", use_container_width=True):
                st.session_state.user_step -= 1
                st.rerun()

    with col_fwd:
        if step < 4:
            if st.button("Next  ➡", type="primary", use_container_width=True):
                st.session_state.user_step += 1
                st.rerun()

# PAGE: BOT
def page_bot():
    p = get_user_profile()

    st.markdown("# 🤖 AI Financial Advisor")

    # Profile not set warning
    if p.get("income", 0) == 0:
        st.warning(
            "⚙️ Your profile isn't set up yet. Go to **USER** to add your income "
            "and expenses so I can give you personalised advice.",
            icon="⚠️"
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Welcome message on first load
    if not st.session_state.messages:
        name = p.get("name", "")
        welcome = (
            f"👋 Welcome {'back, ' + name + '!' if name else 'to MoneyBOT!'}\n\n"
            "I'm your AI Financial Advisor. Here's what I can help with:\n\n"
            "💬 **Try asking me:**\n"
            "• `show my balance`\n"
            "• `spent 500 on food`\n"
            "• `where should I invest?`\n"
            "• `show monthly analysis`\n"
            "• `I want to save for a bike`"
        )
        st.session_state.messages.append({
            "role": "assistant", "content": welcome
        })

    # Render chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ask about your finances...")

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get response
        response = chatbot(user_input)

        # Add bot response
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Rerun to display (avoids double-render bug)
        st.rerun()

    # Clear chat button
    if st.session_state.messages:
        if st.button("🗑  Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

# PAGE: VISUALIZATION
def page_visualization():
    p = get_user_profile()
    st.markdown("# 📊 Visualization")
    st.markdown("<hr>", unsafe_allow_html=True)

    if p.get("income", 0) == 0:
        st.info("⚙️ Set up your profile first to see your financial charts.")
        return

    tab1, tab2, tab3 = st.tabs(["💰  Income vs Expenses  ", "  📂  Category Breakdown  ", "  📈  Investment Allocation"])

    with tab1:
        inc   = p.get("income", 0)
        spent = p.get("monthly_spent", 0)
        saved = p.get("savings", 0)

        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            # Donut chart: spent vs saved
            fig = go.Figure(go.Pie(
                labels=["Spent", "Saved"],
                values=[spent, max(saved, 0)],
                hole=0.65,
                marker=dict(colors=["#e74c3c", "#3ddc84"],
                            line=dict(color="#0e1a14", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#e8f5ec", size=12),
                hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>"
            ))
            fig.update_layout(
                title=dict(text="Monthly Budget Split", font=dict(color="#9dbda8")),
                showlegend=False,
                annotations=[dict(
                    text=f"₹{inc:,.0f}<br><span style='font-size:10px'>income</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=14, color="#3ddc84")
                )],
                **PLOTLY_LAYOUT
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Waterfall
            fig2 = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute", "relative", "total"],
                x=["Income", "Expenses", "Savings"],
                y=[inc, -spent, 0],
                connector=dict(line=dict(color="#2d4a35")),
                decreasing=dict(marker=dict(color="#e74c3c")),
                increasing=dict(marker=dict(color="#3ddc84")),
                totals=dict(marker=dict(color="#27ae60")),
                text=[f"₹{inc:,.0f}", f"-₹{spent:,.0f}", f"₹{max(saved,0):,.0f}"],
                textposition="outside",
                textfont=dict(color="#e8f5ec"),
            ))
            fig2.update_layout(
                title=dict(text="Monthly Cash Flow", font=dict(color="#9dbda8")),
                yaxis=dict(gridcolor="#162318", tickprefix="₹"),
                xaxis=dict(gridcolor="#162318"),
                showlegend=False,
                **PLOTLY_LAYOUT
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        # Category spending breakdown
        cat_fields = {
            "Groceries":     p.get("groceries", 0),
            "Food/Dining":   p.get("food", 0),
            "Travel":        p.get("travel", 0),
            "Entertainment": p.get("entertainment", 0),
            "Bills":         p.get("bills", 0),
            "Shopping":      p.get("shopping", 0),
            "Health":        p.get("health", 0),
            "Misc":          p.get("misc", 0),
        }

        tracked_total = sum(cat_fields.values())
        necessary     = p.get("necessary", 0)
        leisure       = p.get("leisure", 0)

        if necessary > 0 and tracked_total < necessary:
            remainder = necessary - tracked_total
            if remainder > 50:
                cat_fields["Other Necessary"] = remainder
        elif necessary > 0 and tracked_total == 0:
            cat_fields["Necessary (profile)"] = necessary

        if leisure > 0 and tracked_total == 0:
            cat_fields["Leisure (profile)"] = leisure

        df_cat = pd.DataFrame({"Category": list(cat_fields.keys()),
                               "Amount":   list(cat_fields.values())})
        df_cat = df_cat[df_cat["Amount"] > 0].reset_index(drop=True)

        if df_cat.empty:
            st.info("No expense data yet. Add expenses via chat or set up your profile.")
        else:
            CAT_COLORS = {
                "Groceries":            "#3ddc84",
                "Food/Dining":          "#f39c12",
                "Travel":               "#3498db",
                "Entertainment":        "#9b59b6",
                "Bills":                "#e74c3c",
                "Shopping":             "#1abc9c",
                "Health":               "#e67e22",
                "Misc":                 "#95a5a6",
                "Necessary (profile)":  "#27ae60",
                "Leisure (profile)":    "#f1c40f",
                "Other Necessary":      "#2ecc71",
            }

            col1, col2 = st.columns(2)
            with col1:
                df_sorted = df_cat.sort_values("Amount")
                s_colors  = [CAT_COLORS.get(c, "#5a8a68") for c in df_sorted["Category"]]
                fig = go.Figure(go.Bar(
                    x=df_sorted["Amount"],
                    y=df_sorted["Category"],
                    orientation="h",
                    marker=dict(color=s_colors, line=dict(color="#0e1a14", width=1)),
                    text=[f"₹{v:,.0f}" for v in df_sorted["Amount"]],
                    textposition="outside",
                    textfont=dict(color="#e8f5ec", size=11),
                ))
                fig.update_layout(
                    title=dict(text="Spending by Category", font=dict(color="#9dbda8")),
                    xaxis=dict(gridcolor="#1c2d21", tickprefix="₹"),
                    yaxis=dict(gridcolor="#1c2d21"),
                    **PLOTLY_LAYOUT
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                pie_colors = [CAT_COLORS.get(c, "#5a8a68") for c in df_cat["Category"]]
                fig2 = go.Figure(go.Pie(
                    labels=df_cat["Category"].tolist(),
                    values=df_cat["Amount"].tolist(),
                    hole=0.5,
                    marker=dict(colors=pie_colors, line=dict(color="#0e1a14", width=2)),
                    textinfo="label+percent",
                    textfont=dict(color="#ffffff", size=12),
                    hovertemplate="%{label}: ₹%{value:,.0f}<extra></extra>"
                ))
                fig2.update_layout(
                    title=dict(text="Category Share", font=dict(color="#9dbda8")),
                    showlegend=True,
                    legend=dict(font=dict(color="#9dbda8", size=10),
                                bgcolor="rgba(0,0,0,0)"),
                    **PLOTLY_LAYOUT
                )
                st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        # Show investment allocation from the expert engine
        from chatbot_backend import build_expert_input
        from investment_engine import investment_expert
        result = investment_expert(build_expert_input(p))
        alloc  = result["allocation"]

        INVEST_COLORS = {
            "Equity":                "#3ddc84",
            "Mutual Fund":           "#3498db",
            "Fixed Deposits":        "#e74c3c",
            "Public Provident Fund": "#f39c12",
            "Gold":                  "#ffd700",
        }
        colors = [INVEST_COLORS.get(k, "#5a8a68") for k in alloc]

        col1, col2 = st.columns([3, 2], gap="large")

        with col1:
            fig = go.Figure(go.Pie(
                labels=list(alloc.keys()),
                values=list(alloc.values()),
                hole=0.50,
                marker=dict(
                    colors=colors,
                    line=dict(color="#0e1a14", width=3)
                ),
                textinfo="label+percent",
                textfont=dict(color="#ffffff", size=13, family="DM Sans"),
                insidetextorientation="auto",
                hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>",
                pull=[0.04 if i == 0 else 0 for i in range(len(alloc))],
            ))
            fig.update_layout(
                title=dict(
                    text="Recommended Allocation",
                    font=dict(color="#9dbda8", size=14)
                ),
                showlegend=True,
                legend=dict(
                    font=dict(color="#9dbda8", size=12, family="DM Sans"),
                    bgcolor="rgba(0,0,0,0)",
                    orientation="v",
                    yanchor="middle", y=0.5,
                    xanchor="left",  x=1.02,
                ),
                **PLOTLY_LAYOUT
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Allocation legend with color dots
            st.markdown("""
            <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
                        color:#5a8a68; text-transform:uppercase; letter-spacing:1.5px;
                        margin-bottom:1rem; padding-top:0.5rem">
                Allocation
            </div>
            """, unsafe_allow_html=True)

            for avenue, pct in alloc.items():
                c = INVEST_COLORS.get(avenue, "#5a8a68")
                bar_w = min(pct, 100)
                st.markdown(f"""
                <div style="margin-bottom:0.75rem">
                    <div style="display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:4px">
                        <div style="display:flex; align-items:center; gap:8px">
                            <div style="width:10px; height:10px; border-radius:50%;
                                         background:{c}; flex-shrink:0"></div>
                            <span style="font-family:'DM Sans',sans-serif;
                                          font-size:0.82rem; color:#e8f5ec;
                                          font-weight:600">{avenue}</span>
                        </div>
                        <span style="font-family:'Space Mono',monospace;
                                      font-size:0.82rem; color:{c};
                                      font-weight:700">{pct}%</span>
                    </div>
                    <div style="background:#2d4a35; border-radius:99px; height:4px">
                        <div style="width:{bar_w}%; height:100%; border-radius:99px;
                                     background:{c}"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Reasoning section
            st.markdown("""
            <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
                        color:#5a8a68; text-transform:uppercase; letter-spacing:1.5px;
                        margin:1.4rem 0 0.8rem 0">
                Why this plan
            </div>
            """, unsafe_allow_html=True)

            for r in result["reasons"]:
                st.markdown(f"""
                <div style="display:flex; gap:10px; margin-bottom:0.6rem;
                             align-items:flex-start">
                    <div style="color:#3ddc84; font-size:0.75rem; margin-top:2px;
                                 flex-shrink:0; font-family:'Space Mono',monospace">→</div>
                    <div style="font-size:0.8rem; color:#9dbda8; line-height:1.55;
                                 font-family:'DM Sans',sans-serif">{r}</div>
                </div>
                """, unsafe_allow_html=True)

            if result["warnings"]:
                st.markdown("""
                <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
                            color:#f39c12; text-transform:uppercase; letter-spacing:1.5px;
                            margin:1.2rem 0 0.7rem 0">
                    ⚠️ Action needed first
                </div>
                """, unsafe_allow_html=True)
                for w in result["warnings"]:
                    st.markdown(f"""
                    <div style="background:rgba(243,156,18,0.1);
                                 border:1px solid rgba(243,156,18,0.4);
                                 border-left:3px solid #f39c12;
                                 border-radius:8px; padding:9px 12px;
                                 font-size:0.8rem; color:#f5c842;
                                 margin-bottom:6px;
                                 font-family:'DM Sans',sans-serif;
                                 line-height:1.5">{w}</div>
                    """, unsafe_allow_html=True)

# PAGE: MODEL EVALUATION
def page_model_evaluation():
    st.markdown("# 📈 Model Evaluation")
    st.markdown("<hr>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🤖  NLP Model  ", "  📊  Investment Engine"])

    with tab1:
        st.markdown("### DistilBERT Intent Classifier")

        # ── Top-line metrics from actual evaluation run 
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Accuracy",  "97.15%", "on 316 val samples")
        with c2:
            metric_card("Macro F1",  "97.14%", "all 13 classes")
        with c3:
            metric_card("Errors",    "9 / 316", "2.85% error rate")
        with c4:
            metric_card("High-Conf", "99.0%",  "correct preds ≥85%")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Per-class F1 bar chart 
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#5a8a68;
                    text-transform:uppercase; letter-spacing:1.5px; margin-bottom:0.8rem">
            Per-Class F1 · Precision · Recall
        </div>
        """, unsafe_allow_html=True)

        eval_data = [
            ("category_expense",             1.000, 1.000, 1.000, 22),
            ("risk_assessment",              1.000, 1.000, 1.000, 25),
            ("add_expense",                  1.000, 0.966, 0.982, 29),
            ("investment_advice",            0.964, 1.000, 0.982, 27),
            ("goal_setting",                 0.962, 1.000, 0.980, 25),
            ("goodbye",                      1.000, 0.958, 0.979, 24),
            ("investment_recommendation_ml", 1.000, 0.957, 0.978, 23),
            ("add_income",                   0.952, 1.000, 0.976, 20),
            ("greeting",                     0.962, 0.962, 0.962, 26),
            ("monthly_analysis",             0.958, 0.958, 0.958, 24),
            ("check_total_expense",          0.955, 0.955, 0.955, 22),
            ("check_income",                 0.923, 0.960, 0.941, 25),
            ("check_balance",                0.957, 0.917, 0.936, 24),
        ]
        intents  = [r[0] for r in eval_data]
        f1s      = [r[3] for r in eval_data]
        precs    = [r[1] for r in eval_data]
        recs     = [r[2] for r in eval_data]
        supports = [r[4] for r in eval_data]
        bar_cols = ["#3ddc84" if f >= 0.97 else "#f39c12" if f >= 0.95 else "#e74c3c"
                    for f in f1s]

        fig_eval = go.Figure()
        fig_eval.add_trace(go.Bar(
            x=f1s, y=intents, orientation="h",
            marker=dict(color=bar_cols, line=dict(color="#0e1a14", width=1)),
            text=[f"F1={f:.3f}  P={p:.3f}  R={r:.3f}  n={n}"
                  for f, p, r, n in zip(f1s, precs, recs, supports)],
            textposition="outside",
            textfont=dict(color="#9dbda8", size=9),
            hovertemplate="<b>%{y}</b><br>F1=%{x:.3f}<extra></extra>",
        ))
        fig_eval.add_vline(x=0.97, line_dash="dash", line_color="#3ddc84",
                           line_width=1, opacity=0.5)
        fig_eval.update_layout(
            height=460,
            xaxis=dict(range=[0.88, 1.10], gridcolor="#1c2d21",
                       title="Score", tickformat=".2f"),
            yaxis=dict(gridcolor="#1c2d21", categoryorder="array",
                       categoryarray=intents),
            showlegend=False,
            title=dict(text="F1 · Precision · Recall per Intent (sorted by F1)",
                       font=dict(color="#9dbda8", size=12)),
            **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_eval, use_container_width=True)

        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            metric_card("Avg Conf (correct)", "97.7%", "model very sure when right")
        with cc2:
            metric_card("Avg Conf (wrong)",   "61.9%", "uncertain when wrong ✅")
        with cc3:
            metric_card("≥85% conf correct",  "99.0%", "of all correct predictions")

        st.markdown("""
        <div style="background:rgba(61,220,132,0.07); border:1px solid #2d4a35;
                    border-left:3px solid #3ddc84; border-radius:8px;
                    padding:10px 14px; margin:1rem 0;
                    font-size:0.82rem; color:#9dbda8;
                    font-family:'DM Sans',sans-serif; line-height:1.6">
            <strong style="color:#3ddc84">What this means:</strong>
            97.15% accuracy on 13 classes is production-ready. The 9 errors
            are all on semantically ambiguous queries and have low confidence
            (avg 61.9%) — the model knows when it is uncertain. Only 1 error
            was high-confidence (<em>"which investment is right for me"</em> at 98%)
            but both investment intents map to the same handler, so it has no
            real effect on the app.
        </div>
        """, unsafe_allow_html=True)

        # ── Misclassification table 
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#5a8a68;
                    text-transform:uppercase; letter-spacing:1.5px; margin-bottom:0.8rem">
            All 9 Misclassified Examples
        </div>
        """, unsafe_allow_html=True)

        errors = [
            ("gifted 2000 to someone",           "add_expense",                "add_income",               0.66),
            ("help me with my money",            "greeting",                   "check_balance",            0.40),
            ("total debit this month",           "check_total_expense",        "check_income",             0.50),
            ("how much money is in my account",  "check_balance",              "check_income",             0.57),
            ("how much room do I have to spend", "check_balance",              "check_total_expense",      0.47),
            ("month I saved most",               "monthly_analysis",           "goal_setting",             0.61),
            ("thanks for help",                  "goodbye",                    "greeting",                 0.93),
            ("which investment is right for me", "investment_recommendation_ml","investment_advice",       0.98),
            ("inflow this month",                "check_income",               "monthly_analysis",         0.43),
        ]
        rows_html = ""
        for text, true, pred, conf in errors:
            conf_color = "#e74c3c" if conf >= 0.85 else "#f39c12"
            note       = " ⚠️" if conf >= 0.85 else ""
            rows_html += f"""
            <tr style="border-bottom:1px solid #2d4a35">
                <td style="padding:8px 12px; color:#e8f5ec; font-size:0.79rem;
                           font-family:'DM Sans',sans-serif">{text}</td>
                <td style="padding:8px 12px; color:#3ddc84; font-size:0.75rem;
                           font-family:'Space Mono',monospace">{true}</td>
                <td style="padding:8px 12px; color:#e74c3c; font-size:0.75rem;
                           font-family:'Space Mono',monospace">{pred}</td>
                <td style="padding:8px 12px; color:{conf_color}; font-size:0.78rem;
                           font-family:'Space Mono',monospace; text-align:center">
                    {conf:.2f}{note}</td>
            </tr>"""

        st.markdown(f"""
        <div style="background:#1c2d21; border:1px solid #2d4a35; border-radius:10px;
                    overflow:hidden; margin-bottom:6px">
            <table style="width:100%; border-collapse:collapse">
                <thead>
                    <tr style="background:#162318">
                        <th style="padding:9px 12px; text-align:left; color:#3ddc84;
                                   font-family:'Space Mono',monospace; font-size:0.68rem;
                                   letter-spacing:1px; border-bottom:1px solid #2d4a35">Query</th>
                        <th style="padding:9px 12px; text-align:left; color:#3ddc84;
                                   font-family:'Space Mono',monospace; font-size:0.68rem;
                                   letter-spacing:1px; border-bottom:1px solid #2d4a35">True Intent</th>
                        <th style="padding:9px 12px; text-align:left; color:#3ddc84;
                                   font-family:'Space Mono',monospace; font-size:0.68rem;
                                   letter-spacing:1px; border-bottom:1px solid #2d4a35">Predicted As</th>
                        <th style="padding:9px 12px; text-align:center; color:#3ddc84;
                                   font-family:'Space Mono',monospace; font-size:0.68rem;
                                   letter-spacing:1px; border-bottom:1px solid #2d4a35">Conf</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        <div style="font-size:0.73rem; color:#5a8a68; font-family:'DM Sans',sans-serif">
            ⚠️ = overconfident error &nbsp;|&nbsp;
            orange = low-confidence error (model was uncertain — acceptable)
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Class distribution (training data) 
        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#5a8a68;
                    text-transform:uppercase; letter-spacing:1.5px; margin-bottom:0.8rem">
            Training Data — Class Distribution
        </div>
        """, unsafe_allow_html=True)

        classes = ["greeting","goodbye","add_expense","check_total_expense","category_expense","monthly_analysis","add_income","check_balance","investment_advice","investment_recommendation_ml","risk_assessment","goal_setting","check_income"]
        counts = [128,119,144,111,111,122,103,120,133,117,123,124,123]

        fig_dist = go.Figure(go.Bar(
            x=counts, y=classes, orientation="h",
            marker=dict(
                color=counts,
                colorscale=[[0,"#162318"],[0.5,"#27ae60"],[1,"#3ddc84"]],
                line=dict(color="#0e1a14", width=1)
            ),
            text=[str(c) for c in counts],
            textposition="outside",
            textfont=dict(color="#9dbda8", size=10),
        ))
        fig_dist.update_layout(
            height=420,
            yaxis=dict(gridcolor="#1c2d21"),
            xaxis=dict(gridcolor="#1c2d21", title="Patterns"),
            **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with tab2:
        st.markdown("### Rule-Based Investment Expert")
        st.markdown("""
        The ML model (Random Forest + CatBoost) on `Finance_Trends.csv` was abandoned
        after statistical analysis proved the dataset labels were **randomly generated**.
        """)

        c1, c2 = st.columns(2)
        with c1:
            metric_card("ML Accuracy", "24%", "= random guessing (4 classes)")
        with c2:
            metric_card("Rule Engine", "100%", "financially consistent results")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Why ML failed on this dataset")

        features = ["gender","Factor","Objective","Purpose","Duration","Invest_Monitor","Expect","Savings Objectives","Reason_Equity","Reason_Mutual","Reason_Bonds","Reason_FD","Investment_Avenues"]
        p_vals   = [0.135,0.416,0.315,0.296,0.334,0.716,0.832,0.177,0.388,0.250,0.245,0.344,0.665]

        fig = go.Figure(go.Bar(
            x=p_vals, y=features, orientation="h",
            marker=dict(
                color=["#e74c3c" if p > 0.05 else "#3ddc84" for p in p_vals],
                line=dict(color="#0e1a14", width=1)
            ),
            text=[f"p={p:.3f}" for p in p_vals],
            textposition="outside",
            textfont=dict(color="#9dbda8", size=10),
        ))
        fig.add_vline(x=0.05, line_dash="dash", line_color="#3ddc84",
                      annotation_text="p=0.05 threshold",
                      annotation_font_color="#3ddc84")
        fig.update_layout(
            title=dict(text="Chi² p-value per feature vs Avenue label (all > 0.05 = no signal)", font=dict(color="#9dbda8")),
            xaxis=dict(title="p-value", gridcolor="#1c2d21"),
            yaxis=dict(gridcolor="#1c2d21"),
            height=420,
            **PLOTLY_LAYOUT
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        <div style="font-family:'Space Mono',monospace; font-size:0.72rem; color:#5a8a68;
                    text-transform:uppercase; letter-spacing:1.5px; margin:1.5rem 0 1rem 0">
            Rule Engine Structure
        </div>
        """, unsafe_allow_html=True)

        # Gates — danger/warning style
        gates = [
            ("GATE 1", "No Emergency Fund", "If savings rate < 10%, invest in Fixed Deposits first to build a 3–6 month buffer before any market exposure.", "#e74c3c", "🛡️"),
            ("GATE 2", "Active Debt", "When debt is detected, all allocation scores are reduced ×0.6. Clear high-interest loans first — that's a guaranteed 18–24% return.", "#f39c12", "⚠️"),
        ]
        for tag, title, desc, color, icon in gates:
            st.markdown(f"""
            <div style="background:rgba({','.join(str(int(color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.1);
                         border:1px solid {color}; border-left:4px solid {color};
                         border-radius:10px; padding:12px 16px; margin-bottom:10px;
                         display:flex; gap:14px; align-items:flex-start">
                <div style="background:{color}; color:#0e1a14; font-family:'Space Mono',monospace;
                             font-weight:700; font-size:0.68rem; padding:3px 8px; border-radius:6px;
                             flex-shrink:0; margin-top:2px; white-space:nowrap">
                    {icon} {tag}
                </div>
                <div>
                    <div style="color:#e8f5ec; font-weight:700; font-size:0.88rem;
                                 font-family:'DM Sans',sans-serif; margin-bottom:3px">{title}</div>
                    <div style="color:#9dbda8; font-size:0.78rem; font-family:'DM Sans',sans-serif;
                                 line-height:1.55">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        rules_data = [
            ("RULE 1", "Age Bands", "5 tiers", "<25 → equity-heavy | 25–34 → growth | 35–44 → balanced | 45–54 → preservation | 55+ → safety", "#3ddc84"),
            ("RULE 2", "Risk Tolerance", "3 levels", "Low → FD + PPF + Gold | Medium → Mutual funds + PPF | High → Equity + MF", "#3498db"),
            ("RULE 3", "Investment Horizon", "4 tiers", "<1 yr → liquid FD | 1–3 yr → FD + Gold | 3–5 yr → Mutual funds | >5 yr → Equity + PPF", "#9b59b6"),
            ("RULE 4", "Return Expectation", "3 bands", "10–20% → FD/PPF | 20–30% → Equity MF / SIP | 30–40% → Direct equity", "#f39c12"),
            ("RULE 5", "Primary Objective", "3 types", "Income → FD + PPF | Growth → Mutual funds | Capital Appreciation → Equity", "#1abc9c"),
            ("RULE 6", "Savings Goal", "5 goals", "Retirement → PPF | Health → FD + Gold | Education → MF + PPF | Wealth → Equity | Future → FD + MF", "#e67e22"),
            ("RULE 7", "Savings Rate", "2 special cases", "<15% → prioritise safety (FD +2) | >35% → can absorb volatility (Equity +2, MF +2)", "#95a5a6"),
        ]

        cols = st.columns(2)
        for i, (tag, title, badge, desc, color) in enumerate(rules_data):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background:#1c2d21; border:1px solid #2d4a35;
                             border-top:3px solid {color};
                             border-radius:10px; padding:12px 14px; margin-bottom:10px">
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                 margin-bottom:6px">
                        <div style="display:flex; gap:8px; align-items:center">
                            <span style="background:{color}22; color:{color};
                                          font-family:'Space Mono',monospace; font-weight:700;
                                          font-size:0.65rem; padding:2px 7px; border-radius:5px">
                                {tag}
                            </span>
                            <span style="color:#e8f5ec; font-weight:600; font-size:0.86rem;
                                          font-family:'DM Sans',sans-serif">{title}</span>
                        </div>
                        <span style="color:{color}; font-size:0.7rem; font-family:'DM Sans',sans-serif;
                                      background:{color}15; padding:2px 8px; border-radius:99px">
                            {badge}
                        </span>
                    </div>
                    <div style="color:#9dbda8; font-size:0.75rem; font-family:'DM Sans',sans-serif;
                                 line-height:1.6; border-top:1px solid #2d4a35; padding-top:8px">
                        {desc}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# PAGE: GOAL TRACKING
def page_goals():
    p = get_user_profile()
    st.markdown("# 🎯 Goal Tracking")
    st.markdown("<hr>", unsafe_allow_html=True)

    monthly_savings = p.get("savings", 0)

    with st.expander("➕  Add a New Goal", expanded=len(p.get("goals", [])) == 0):
        c1, c2, c3 = st.columns(3)
        with c1:
            goal_name   = st.text_input("Goal name", placeholder="e.g. New Bike")
        with c2:
            goal_amount = st.number_input("Target amount (₹)", min_value=1000,
                                          max_value=10_000_000, value=50000, step=1000)
        with c3:
            goal_months = st.number_input("Target months", min_value=1,
                                          max_value=120, value=12, step=1)

        if st.button("Add Goal", type="primary"):
            if goal_name:
                if "goals" not in st.session_state.user_profile:
                    st.session_state.user_profile["goals"] = []
                st.session_state.user_profile["goals"].append({
                    "name":       goal_name,
                    "target":     goal_amount,
                    "months":     goal_months,
                    "saved":      0,
                })
                st.success(f"Goal '{goal_name}' added!")
                st.rerun()
            else:
                st.warning("Please enter a goal name.")

    goals = p.get("goals", [])

    if not goals:
        st.info("No goals yet. Add your first financial goal above!")
        if monthly_savings > 0:
            st.markdown("### What can you save?")
            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("In 6 months",  f"₹{monthly_savings*6:,.0f}", f"₹{monthly_savings:,.0f}/mo")
            with c2:
                metric_card("In 1 year",    f"₹{monthly_savings*12:,.0f}", f"₹{monthly_savings:,.0f}/mo")
            with c3:
                metric_card("In 3 years",   f"₹{monthly_savings*36:,.0f}", f"₹{monthly_savings:,.0f}/mo")
        return

    st.markdown(f"### Your Goals ({len(goals)})")

    for i, goal in enumerate(goals):
        target  = goal["target"]
        saved   = goal.get("saved", 0)
        months  = goal["months"]
        pct     = min(int(saved / target * 100), 100) if target else 0

        needed_per_month = (target - saved) / months if months else target
        feasible = monthly_savings >= needed_per_month

        color   = "#3ddc84" if pct >= 80 else "#f39c12" if pct >= 40 else "#e74c3c"
        f_label = "✅ On track" if feasible else "⚠️ Need to save more"

        with st.container():
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:0.8rem">
                <div style="display:flex; justify-content:space-between; align-items:flex-start">
                    <div>
                        <div class="metric-label">{goal['name']}</div>
                        <div class="metric-value" style="font-size:1.1rem; color:{color}">₹{saved:,.0f} / ₹{target:,.0f}</div>
                        <div class="metric-sub">{f_label} · ₹{needed_per_month:,.0f}/mo needed · {months} months</div>
                    </div>
                    <div style="font-size:1.6rem; color:{color}; font-family:'Space Mono',monospace; font-weight:700">{pct}%</div>
                </div>
                <div class="stat-bar-bg" style="margin-top:12px">
                    <div class="stat-bar-fill" style="width:{pct}%; background:{'linear-gradient(90deg,#27ae60,#3ddc84)' if pct>=40 else 'linear-gradient(90deg,#c0392b,#e74c3c)'}"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_add, col_del = st.columns([3, 1])
            with col_add:
                add_amt = st.number_input(
                    f"Add savings to '{goal['name']}'",
                    min_value=0, max_value=int(target - saved + 1),
                    value=0, step=500, key=f"goal_add_{i}",
                    label_visibility="collapsed"
                )
                if add_amt > 0:
                    if st.button(f"+ Add ₹{add_amt:,}", key=f"btn_add_{i}"):
                        st.session_state.user_profile["goals"][i]["saved"] += add_amt
                        st.rerun()
            with col_del:
                if st.button("🗑 Remove", key=f"btn_del_{i}"):
                    st.session_state.user_profile["goals"].pop(i)
                    st.rerun()

# PAGE: NEWS (placeholder with real financial topics)
def page_news():
    st.markdown("# 📰 Finance News & Tips")
    st.markdown("<hr>", unsafe_allow_html=True)

    st.info("🔗 Live news feed coming soon. Here are curated financial tips for now.")
    st.markdown("<br>", unsafe_allow_html=True)

    tips = [
        ("💡 50/30/20 Rule", "Allocate 50% of income to needs, 30% to wants, and 20% to savings & investments. It's the most widely recommended budgeting framework.", "#3ddc84"),
        ("📈 Start SIP Early", "₹1,000/month in an index fund at age 25 → ₹35L+ at 55 (assuming 12% CAGR). At age 35, the same amount yields only ₹10L. Time is your biggest asset.", "#27ae60"),
        ("🛡️ Emergency Fund First", "Before investing, build 3–6 months of expenses in a liquid instrument. Without this, any market correction may force you to sell investments at a loss.", "#f39c12"),
        ("💳 Debt Before Investment", "Credit card interest is typically 36–42% per year. No investment reliably beats this. Pay off high-interest debt before putting money in markets.", "#e74c3c"),
        ("🪙 Gold as Hedge", "Gold typically moves opposite to equity. A 5–10% gold allocation reduces portfolio volatility without significantly impacting returns.", "#ffd700"),
        ("📊 PPF: The Hidden Gem", "PPF offers ~7.1% tax-free returns with 80C benefit. The effective post-tax return for someone in the 30% bracket is ~10.1% — better than most FDs.", "#1a8a40"),
    ]

    col1, col2 = st.columns(2)
    for i, (title, body, color) in enumerate(tips):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom:0.9rem; border-left:3px solid {color}">
                <div style="font-family:'DM Sans',sans-serif; font-weight:600; color:#e8f5ec; font-size:0.95rem; margin-bottom:6px">{title}</div>
                <div style="font-size:0.82rem; color:#9dbda8; line-height:1.55">{body}</div>
            </div>
            """, unsafe_allow_html=True)

# MAIN ROUTER
render_sidebar()
page = st.session_state.current_page

if   page == "About Project":   page_about()
elif page == "USER":             page_user()
elif page == "BOT":              page_bot()
elif page == "Visualization":    page_visualization()
elif page == "Model Evaluation": page_model_evaluation()
elif page == "Goal Tracking":    page_goals()
elif page == "News":             page_news()
else:
    st.error(f"Unknown page: {page}")
