import streamlit as st
import time
import os
import json
import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv(override=True)

# ─── Page Config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import (init_db, create_session, save_answer, end_session,
                       get_user_sessions, get_session_answers,
                       get_user_stats, get_score_history)
from auth import signup, login
from interview_bot import (generate_question, evaluate_answer,
                            generate_session_summary, transcribe_audio,
                            ROLES, DOMAINS, TOP_COMPANIES,
                            DIFFICULTY_LEVELS, EXPERIENCE_LEVELS)
from resume_parser import parse_resume

init_db()

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0a0f1e; color: #e2e8f0; }
#MainMenu, footer, .stDeployButton { visibility: hidden; }
header[data-testid="stHeader"] {
    background: rgba(10,15,30,0.95);
    border-bottom: 1px solid rgba(99,102,241,0.2);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0d1425 0%,#111827 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}

/* Cards */
.card {
    background: linear-gradient(135deg,#111827 0%,#1a2035 100%);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: rgba(99,102,241,0.5); }

/* Stat cards */
.stat-card {
    background: linear-gradient(135deg,#1e1b4b 0%,#312e81 100%);
    border: 1px solid rgba(129,140,248,0.3);
    border-radius: 14px; padding: 1.2rem 1.5rem; text-align: center;
}
.stat-card .value { font-size:2rem; font-weight:800; color:#a5b4fc; line-height:1; }
.stat-card .label { font-size:0.78rem; color:#94a3b8; margin-top:0.3rem;
                    letter-spacing:0.05em; text-transform:uppercase; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%);
    color: white; border: none; border-radius: 10px;
    padding: 0.6rem 1.4rem; font-weight: 600; font-size: 0.9rem;
    transition: all 0.2s; width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(99,102,241,0.4);
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: #1a2035 !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 10px !important; color: #e2e8f0 !important;
}

/* Question box */
.question-box {
    background: linear-gradient(135deg,#1e1b4b 0%,#1e293b 100%);
    border-left: 4px solid #6366f1; border-radius: 0 14px 14px 0;
    padding: 1.5rem; margin: 1rem 0; font-size: 1.05rem; line-height: 1.7;
}

/* Voice box */
.voice-box {
    background: linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%);
    border: 2px dashed rgba(99,102,241,0.4);
    border-radius: 14px; padding: 1.5rem; margin: 0.5rem 0; text-align: center;
}
.voice-active {
    border-color: #ef4444 !important;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%   { box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }
    70%  { box-shadow: 0 0 0 10px rgba(239,68,68,0); }
    100% { box-shadow: 0 0 0 0 rgba(239,68,68,0); }
}

/* Feedback sections */
.feedback-strength { background:#052e16; border:1px solid #16a34a; border-radius:10px; padding:1rem; margin:0.4rem 0; }
.feedback-weakness { background:#450a0a; border:1px solid #dc2626; border-radius:10px; padding:1rem; margin:0.4rem 0; }
.feedback-model    { background:#0c1445; border:1px solid #3b82f6; border-radius:10px; padding:1rem; margin:0.4rem 0; }
.feedback-tip      { background:#1c1427; border:1px solid #8b5cf6; border-radius:10px; padding:1rem; margin:0.4rem 0; }

/* Score badges */
.score-excellent { background:linear-gradient(135deg,#065f46,#047857); color:#6ee7b7; border:1px solid #10b981; border-radius:8px; padding:0.3rem 0.8rem; font-weight:700; display:inline-block; }
.score-good      { background:linear-gradient(135deg,#1e3a5f,#1d4ed8); color:#93c5fd; border:1px solid #3b82f6; border-radius:8px; padding:0.3rem 0.8rem; font-weight:700; display:inline-block; }
.score-average   { background:linear-gradient(135deg,#78350f,#b45309); color:#fcd34d; border:1px solid #f59e0b; border-radius:8px; padding:0.3rem 0.8rem; font-weight:700; display:inline-block; }
.score-poor      { background:linear-gradient(135deg,#7f1d1d,#b91c1c); color:#fca5a5; border:1px solid #ef4444; border-radius:8px; padding:0.3rem 0.8rem; font-weight:700; display:inline-block; }

/* Progress bar */
.progress-bar-container { background:#1a2035; border-radius:99px; height:8px; margin:0.5rem 0; }
.progress-bar { background:linear-gradient(90deg,#6366f1,#8b5cf6); border-radius:99px; height:8px; transition:width 0.5s ease; }

/* Alerts */
.alert-info    { background:#0c1a3a; border:1px solid #3b82f6; border-radius:10px; padding:1rem; color:#93c5fd; }
.alert-success { background:#052e16; border:1px solid #16a34a; border-radius:10px; padding:1rem; color:#6ee7b7; }
.alert-warning { background:#1c1000; border:1px solid #d97706; border-radius:10px; padding:1rem; color:#fcd34d; }
.alert-error   { background:#2d0a0a; border:1px solid #ef4444; border-radius:10px; padding:1rem; color:#fca5a5; }

/* Auth */
.auth-title    { font-size:2.2rem; font-weight:800; background:linear-gradient(135deg,#a5b4fc,#c4b5fd); -webkit-background-clip:text; -webkit-text-fill-color:transparent; text-align:center; }
.auth-subtitle { text-align:center; color:#64748b; font-size:0.9rem; margin-bottom:2rem; }
.app-logo      { font-size:1.8rem; font-weight:800; background:linear-gradient(135deg,#6366f1,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.app-tagline   { font-size:0.75rem; color:#64748b; letter-spacing:0.08em; text-transform:uppercase; }

/* Misc */
.company-badge { display:inline-block; background:#1e1b4b; border:1px solid rgba(129,140,248,0.4); color:#a5b4fc; border-radius:20px; padding:0.2rem 0.7rem; font-size:0.75rem; margin:0.2rem; }
hr { border-color: rgba(99,102,241,0.15); }
[data-testid="stTabs"] [role="tab"] { color:#64748b; font-weight:500; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { color:#a5b4fc; border-bottom-color:#6366f1; font-weight:700; }
[data-testid="stExpander"] { background:#111827; border:1px solid rgba(99,102,241,0.2); border-radius:10px; }
[data-testid="metric-container"] { background:#111827; border:1px solid rgba(99,102,241,0.2); border-radius:12px; padding:1rem; }
[data-testid="stMetricValue"] { color:#a5b4fc; font-weight:800; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "logged_in": False, "user": None,
        "page": "home",
        "interview_active": False,
        "session_id": None,
        "current_question": None,
        "question_num": 0,
        "previous_questions": [],
        "answers_list": [],
        "evaluation": None,
        "show_evaluation": False,
        "interview_config": {},
        "start_time": None,
        "resume_data": None,
        # Voice input state
        "voice_transcript": "",
        "voice_recorded_q": -1,  # which question the transcript belongs to
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def get_score_color(score):
    if score >= 8: return "#10b981"
    if score >= 6: return "#3b82f6"
    if score >= 4: return "#f59e0b"
    return "#ef4444"

def score_badge_html(score):
    if score >= 8: cls, icon = "score-excellent", "⭐"
    elif score >= 6: cls, icon = "score-good", "👍"
    elif score >= 4: cls, icon = "score-average", "⚠️"
    else: cls, icon = "score-poor", "❌"
    return f'<span class="{cls}">{icon} {score}/10</span>'

def render_progress(current, total):
    pct = int((current / max(total, 1)) * 100)
    st.markdown(f"""
    <div style="margin:0.5rem 0">
      <div style="display:flex;justify-content:space-between;font-size:0.8rem;color:#64748b;margin-bottom:4px">
        <span>Question {current} of {total}</span><span>{pct}% complete</span>
      </div>
      <div class="progress-bar-container">
        <div class="progress-bar" style="width:{pct}%"></div>
      </div>
    </div>""", unsafe_allow_html=True)

def reset_interview_state():
    st.session_state.interview_active  = False
    st.session_state.current_question  = None
    st.session_state.question_num      = 0
    st.session_state.previous_questions = []
    st.session_state.answers_list      = []
    st.session_state.evaluation        = None
    st.session_state.show_evaluation   = False
    st.session_state.voice_transcript  = ""
    st.session_state.voice_recorded_q  = -1

# ─── Auth ─────────────────────────────────────────────────────────────────────
def render_auth():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style="text-align:center;padding-top:2rem;margin-bottom:2rem">
            <div style="font-size:3.5rem">🎯</div>
            <div class="auth-title">AI Interview Coach</div>
            <div class="auth-subtitle">Master your next interview with AI-powered practice</div>
        </div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔑  Login", "✨  Sign Up"])

        with tab1:
            with st.form("login_form"):
                st.markdown("#### Welcome back!")
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                if st.form_submit_button("Login →", use_container_width=True):
                    ok, msg, user = login(username, password)
                    if ok:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        st.error(msg)

        with tab2:
            with st.form("signup_form"):
                st.markdown("#### Create your account")
                c_a, c_b = st.columns(2)
                with c_a: new_user  = st.text_input("Username*", placeholder="Choose a username")
                with c_b: new_email = st.text_input("Email*",    placeholder="your@email.com")
                new_pass  = st.text_input("Password*", type="password",
                                          placeholder="Min 8 chars, 1 uppercase, 1 digit")
                conf_pass = st.text_input("Confirm Password*", type="password",
                                          placeholder="Re-enter password")
                if st.form_submit_button("Create Account →", use_container_width=True):
                    ok, msg = signup(new_user, new_email, new_pass, conf_pass)
                    st.success(msg) if ok else st.error(msg)

        st.markdown("""
        <div style="text-align:center;margin-top:2rem;color:#475569;font-size:0.8rem">
            🔒 Your data is stored locally and securely
        </div>""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1rem 0 0.5rem">
            <div class="app-logo">🎯 AI Coach</div>
            <div class="app-tagline">Interview Preparation Platform</div>
        </div><hr>""", unsafe_allow_html=True)

        user = st.session_state.user
        st.markdown(f"""
        <div style="background:#1a2035;border-radius:12px;padding:0.8rem;margin-bottom:1rem">
            <div style="font-size:1.1rem;font-weight:700;color:#a5b4fc">👤 {user['username']}</div>
            <div style="font-size:0.75rem;color:#64748b;margin-top:2px">{user['email']}</div>
        </div>""", unsafe_allow_html=True)

        pages = {
            "🏠  Dashboard":      "home",
            "🎤  New Interview":  "setup",
            "📊  Analytics":      "analytics",
            "📄  Resume Upload":  "resume",
            "⚙️  Settings":       "settings",
        }
        for label, key in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                if not (st.session_state.interview_active and key not in ("interview",)):
                    st.session_state.page = key
                    st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        stats = get_user_stats(user["id"])
        if (stats.get("total_sessions") or 0) > 0:
            st.markdown("**📈 Your Stats**")
            ca, cb = st.columns(2)
            ca.metric("Sessions", stats.get("total_sessions") or 0)
            cb.metric("Avg Score", f"{(stats.get('overall_avg') or 0):.1f}/10")

        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            init_state()
            st.rerun()

# ─── Dashboard ────────────────────────────────────────────────────────────────
def render_home():
    user     = st.session_state.user
    stats    = get_user_stats(user["id"])
    sessions = get_user_sessions(user["id"])

    st.markdown(f"""
    <div style="margin-bottom:2rem">
        <h1 style="font-size:2.2rem;font-weight:800;color:#e2e8f0;margin-bottom:0.3rem">
            Welcome back, {user['username']} 👋
        </h1>
        <p style="color:#64748b">Ready to ace your next interview? Let's practice!</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in [
        (c1, stats.get("total_sessions") or 0,            "Sessions"),
        (c2, f"{(stats.get('overall_avg') or 0):.1f}",    "Avg Score /10"),
        (c3, f"{(stats.get('best_score')  or 0):.1f}",    "Best Score"),
        (c4, stats.get("total_questions") or 0,           "Questions Done"),
    ]:
        col.markdown(f"""
        <div class="stat-card">
            <div class="value">{val}</div>
            <div class="label">{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([2, 1])

    with left:
        history = get_score_history(user["id"])
        if history:
            st.markdown("#### 📈 Performance History")
            df = pd.DataFrame(history)
            df["date"] = pd.to_datetime(df["started_at"]).dt.strftime("%b %d")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["date"], y=df["avg_score"],
                mode="lines+markers",
                line=dict(color="#6366f1", width=3),
                marker=dict(size=8, color="#a5b4fc"),
                fill="tozeroy", fillcolor="rgba(99,102,241,0.1)",
            ))
            fig.update_layout(
                height=280, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8"),
                yaxis=dict(range=[0,10], gridcolor="rgba(99,102,241,0.1)"),
                xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
                margin=dict(l=0, r=0, t=0, b=0), showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div class="alert-info" style="text-align:center;padding:2rem">
                <div style="font-size:2rem">🚀</div>
                <div style="font-weight:600;margin-top:0.5rem">No sessions yet</div>
                <div style="font-size:0.85rem;margin-top:0.3rem">Start your first interview to see your progress!</div>
            </div>""", unsafe_allow_html=True)

    with right:
        st.markdown("#### 🚀 Quick Start")
        if st.button("▶  Start New Interview", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.resume_data:
            st.markdown('<div class="alert-success">✅ Resume uploaded — questions will be personalised!</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-info">💡 Upload your resume for personalised questions!</div>',
                        unsafe_allow_html=True)
            if st.button("📄 Upload Resume", use_container_width=True):
                st.session_state.page = "resume"
                st.rerun()

    if sessions:
        st.markdown("<br>#### 🕐 Recent Sessions", unsafe_allow_html=True)
        for s in sessions[:5]:
            sc    = s.get("avg_score") or 0
            co    = s.get("company") or "General"
            color = get_score_color(sc)
            st.markdown(f"""
            <div class="card" style="display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style="font-weight:600;color:#e2e8f0">{s['role']} — {s['domain']}</div>
                    <div style="font-size:0.8rem;color:#64748b;margin-top:3px">
                        🏢 {co} &nbsp;|&nbsp; 📅 {s['started_at'][:10]}
                        &nbsp;|&nbsp; ❓ {s['total_questions']} questions
                    </div>
                </div>
                <div style="font-size:1.4rem;font-weight:800;color:{color}">{sc:.1f}/10</div>
            </div>""", unsafe_allow_html=True)

# ─── Interview Setup ──────────────────────────────────────────────────────────
def render_setup():
    st.markdown("""
    <h1 style="font-size:2rem;font-weight:800;color:#e2e8f0;margin-bottom:0.3rem">
        ⚙️ Configure Your Interview
    </h1>
    <p style="color:#64748b">Customise your session for maximum relevance</p><hr>
    """, unsafe_allow_html=True)

    with st.form("interview_setup"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("##### 👤 Role & Domain")
            role_cat   = st.selectbox("Role Category",   list(ROLES.keys()))
            role       = st.selectbox("Specific Role",   ROLES[role_cat])
            domain_cat = st.selectbox("Domain Category", list(DOMAINS.keys()))
            domain     = st.selectbox("Focus Domain",    DOMAINS[domain_cat])

        with col2:
            st.markdown("##### 🎯 Preferences")
            difficulty    = st.select_slider("Difficulty", options=DIFFICULTY_LEVELS, value="Medium")
            experience    = st.selectbox("Experience Level", EXPERIENCE_LEVELS)
            num_questions = st.slider("Number of Questions", 3, 20, 8)

        st.markdown("##### 🏢 Company-Specific Interview")
        mode = st.radio("Mode", ["General Interview", "Company-Specific Interview"], horizontal=True)
        company = "General (No Company Focus)"
        if mode == "Company-Specific Interview":
            comp_cat = st.selectbox("Company Category", list(TOP_COMPANIES.keys()))
            company  = st.selectbox("Select Company",   TOP_COMPANIES[comp_cat])
            if company != "General (No Company Focus)":
                st.markdown(f'<div class="alert-info">🏢 Questions will simulate <strong>{company}</strong> actual interview style.</div>',
                            unsafe_allow_html=True)

        if st.form_submit_button("🚀 Start Interview", use_container_width=True):
            session_id = create_session(
                user_id=st.session_state.user["id"],
                role=role, domain=domain,
                difficulty=difficulty, experience=experience, company=company,
            )
            reset_interview_state()
            st.session_state.session_id       = session_id
            st.session_state.interview_active = True
            st.session_state.interview_config = {
                "role": role, "domain": domain,
                "difficulty": difficulty, "experience": experience,
                "company": company, "num_questions": num_questions,
            }
            st.session_state.page = "interview"
            st.rerun()

# ─── Interview ────────────────────────────────────────────────────────────────
def render_interview():
    cfg          = st.session_state.interview_config
    role         = cfg["role"]
    domain       = cfg["domain"]
    difficulty   = cfg["difficulty"]
    experience   = cfg["experience"]
    company      = cfg["company"]
    num_q        = cfg["num_questions"]
    q_num        = st.session_state.question_num

    # Session complete?
    if q_num >= num_q and not st.session_state.show_evaluation:
        end_session(st.session_state.session_id)
        render_results()
        return

    # Generate question if needed
    if st.session_state.current_question is None and not st.session_state.show_evaluation:
        resume_ctx = ""
        if st.session_state.resume_data:
            rd         = st.session_state.resume_data
            skills_str = ", ".join(rd.get("skills", [])[:10])
            resume_ctx = f"Skills: {skills_str}. Experience: {rd.get('experience_years')} years."

        try:
            with st.spinner("🤔 Generating your next question…"):
                q_data = generate_question(
                    role=role, domain=domain, difficulty=difficulty,
                    experience=experience, company=company,
                    question_num=q_num + 1,
                    previous_questions=st.session_state.previous_questions,
                    resume_context=resume_ctx,
                )
            st.session_state.current_question = q_data
            st.session_state.start_time       = time.time()
            # Clear voice transcript for new question
            st.session_state.voice_transcript = ""
            st.session_state.voice_recorded_q = -1
        except EnvironmentError as e:
            st.error(f"⚙️ **API Key Missing** — {e}")
            st.info("Go to ⚙️ Settings to add your GROQ_API_KEY.")
            st.stop()
        except PermissionError as e:
            st.error(f"🔑 **Invalid API Key** — {e}")
            st.info("Get a free key at https://console.groq.com/keys")
            st.stop()
        except Exception as e:
            st.error(f"❌ **Error generating question**: `{type(e).__name__}: {e}`")
            st.stop()

    if st.session_state.show_evaluation:
        render_evaluation()
        return

    q_data = st.session_state.current_question
    if not q_data:
        return

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
        <div>
            <h2 style="color:#e2e8f0;margin:0">Interview Session</h2>
            <div style="color:#64748b;font-size:0.85rem">
                {role} &nbsp;·&nbsp; {domain} &nbsp;·&nbsp;
                <span style="color:#6366f1">{company}</span>
            </div>
        </div>
        <div style="text-align:right">
            <div style="font-size:0.75rem;color:#64748b">Difficulty</div>
            <div style="font-weight:700;color:#a5b4fc">{difficulty}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    render_progress(q_num + 1, num_q)

    # Question type badge
    qtype  = q_data.get("type", "technical")
    tcolor = {"technical":"#3b82f6","behavioral":"#8b5cf6","system_design":"#10b981",
               "coding":"#f59e0b","situational":"#ec4899"}.get(qtype, "#6366f1")
    st.markdown(f"""
    <div style="margin:0.5rem 0">
        <span style="background:{tcolor}22;color:{tcolor};border:1px solid {tcolor}44;
            border-radius:20px;padding:0.2rem 0.8rem;font-size:0.78rem;font-weight:600;
            text-transform:uppercase;letter-spacing:0.05em">
            {qtype.replace("_"," ")}
        </span>
    </div>""", unsafe_allow_html=True)

    # Question text
    st.markdown(f"""
    <div class="question-box">
        <strong style="color:#a5b4fc;font-size:0.85rem">Question {q_num + 1}</strong>
        <div style="margin-top:0.5rem;font-size:1.05rem;color:#e2e8f0;line-height:1.7">
            {q_data['question']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Hint + topics
    if q_data.get("hint"):
        with st.expander("💡 Need a hint?"):
            st.markdown(f"_{q_data['hint']}_")
    if q_data.get("expected_topics"):
        badges = "".join(f'<span class="company-badge">{t}</span>'
                         for t in q_data["expected_topics"])
        st.markdown(f"<div style='margin:0.5rem 0'><span style='color:#64748b;font-size:0.8rem'>Key topics: </span>{badges}</div>",
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Answer Input: Voice + Text ─────────────────────────────────────────────
    st.markdown("##### ✍️ Your Answer")

    voice_tab, text_tab = st.tabs(["🎤  Speak Your Answer", "⌨️  Type Your Answer"])

    # ── Voice Tab ──────────────────────────────────────────────────────────────
    with voice_tab:
        st.markdown("""
        <div class="alert-info" style="font-size:0.88rem;margin-bottom:1rem">
            🎙️ Click <strong>Start Recording</strong>, speak your answer clearly in English,
            then click <strong>Stop</strong>. Your speech will be automatically transcribed.
        </div>""", unsafe_allow_html=True)

        mic_available = False
        try:
            from streamlit_mic_recorder import mic_recorder
            mic_available = True
        except ImportError:
            st.markdown("""
            <div class="alert-error">
                📦 <strong>streamlit-mic-recorder</strong> is not installed.<br>
                Run: <code>pip install streamlit-mic-recorder</code> then restart the app.
            </div>""", unsafe_allow_html=True)

        if mic_available:
            recording = mic_recorder(
                start_prompt="🔴  Start Recording",
                stop_prompt="⏹  Stop & Transcribe",
                just_once=True,
                use_container_width=True,
                key=f"mic_{q_num}",
            )

            if recording and recording.get("bytes"):
                with st.spinner("🔄 Transcribing your speech via Groq Whisper…"):
                    try:
                        transcript = transcribe_audio(recording["bytes"])
                        if transcript:
                            st.session_state.voice_transcript = transcript
                            st.session_state.voice_recorded_q = q_num
                            st.success("✅ Speech transcribed successfully!")
                        else:
                            st.warning("⚠️ No speech detected. Try again or type your answer.")
                    except Exception as e:
                        st.error(f"❌ Transcription failed: {e}\nPlease type your answer instead.")

            # Show transcript editor if we have one for this question
            if (st.session_state.voice_recorded_q == q_num
                    and st.session_state.voice_transcript):
                st.markdown("**📝 Transcribed Answer** *(edit if needed before submitting)*")
                st.session_state.voice_transcript = st.text_area(
                    "voice_text_edit",
                    value=st.session_state.voice_transcript,
                    height=180,
                    key=f"voice_edit_{q_num}",
                    label_visibility="collapsed",
                )
                if st.button("🗑️ Clear Voice Transcript", key=f"clr_voice_{q_num}"):
                    st.session_state.voice_transcript = ""
                    st.session_state.voice_recorded_q = -1
                    st.rerun()

    # ── Text Tab ───────────────────────────────────────────────────────────────
    with text_tab:
        typed_answer = st.text_area(
            "type_answer",
            height=200,
            placeholder=(
                "Type your answer here…\n\n"
                "• Be specific and structured.\n"
                "• For coding: write your approach + pseudocode / code.\n"
                "• For behavioral: use the STAR method "
                "(Situation → Task → Action → Result).\n"
                "• For system design: start with requirements and scale."
            ),
            key=f"typed_{q_num}",
            label_visibility="collapsed",
        )

    # ── Determine final answer ─────────────────────────────────────────────────
    voice_val  = st.session_state.voice_transcript.strip() \
                 if st.session_state.voice_recorded_q == q_num else ""
    typed_val  = (typed_answer or "").strip()
    user_answer = voice_val if voice_val else typed_val

    # Show which source is active
    if voice_val and typed_val:
        st.info("ℹ️ Both voice and typed answers present — **voice answer** will be submitted. "
                "Clear the transcript to use the typed answer.")
    elif voice_val:
        st.markdown('<div style="font-size:0.82rem;color:#6ee7b7;margin-top:0.3rem">🎤 Voice answer ready to submit</div>',
                    unsafe_allow_html=True)
    elif typed_val:
        st.markdown('<div style="font-size:0.82rem;color:#93c5fd;margin-top:0.3rem">⌨️ Typed answer ready to submit</div>',
                    unsafe_allow_html=True)

    # ── Action buttons ─────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([2, 1, 1])
    with b1: submit_btn = st.button("✅ Submit Answer",  use_container_width=True, key=f"sub_{q_num}")
    with b2: skip_btn   = st.button("⏭ Skip Question",  use_container_width=True, key=f"skp_{q_num}")
    with b3: end_btn    = st.button("🔴 End Session",    use_container_width=True, key=f"end_{q_num}")

    # ── Submit ─────────────────────────────────────────────────────────────────
    if submit_btn:
        if not user_answer or len(user_answer.strip()) < 10:
            st.warning("⚠️ Please provide a meaningful answer (at least 10 characters).")
        else:
            time_taken = int(time.time() - (st.session_state.start_time or time.time()))
            try:
                with st.spinner("🧠 Evaluating your answer…"):
                    evaluation = evaluate_answer(
                        question=q_data["question"],
                        user_answer=user_answer,
                        role=role, domain=domain,
                        difficulty=difficulty,
                        question_type=qtype,
                        expected_topics=q_data.get("expected_topics", []),
                    )
                save_answer(
                    session_id=st.session_state.session_id,
                    user_id=st.session_state.user["id"],
                    question=q_data["question"],
                    question_type=qtype,
                    user_answer=user_answer,
                    score=evaluation["score"],
                    feedback=evaluation["feedback"],
                    correct_answer=evaluation.get("model_answer", ""),
                    improvements=json.dumps(evaluation.get("improvements", [])),
                    time_taken=time_taken,
                )
                st.session_state.previous_questions.append(q_data["question"])
                evaluation["user_answer"] = user_answer
                evaluation["question"]    = q_data["question"]
                evaluation["time_taken"]  = time_taken
                st.session_state.evaluation     = evaluation
                st.session_state.answers_list.append(evaluation)
                st.session_state.show_evaluation = True
                # Clear voice for next question
                st.session_state.voice_transcript = ""
                st.session_state.voice_recorded_q = -1
                st.rerun()
            except EnvironmentError as e:
                st.error(f"⚙️ **API Key Missing** — {e}")
            except PermissionError as e:
                st.error(f"🔑 **Invalid API Key** — {e}")
            except ConnectionError as e:
                st.error(f"🌐 **No Connection** — {e}")
            except RuntimeError as e:
                st.error(f"⚠️ **API Error** — {e}")
            except Exception as e:
                st.error(f"❌ **Unexpected Error**: `{type(e).__name__}: {e}`")

    if skip_btn:
        st.session_state.previous_questions.append(q_data["question"])
        st.session_state.question_num     += 1
        st.session_state.current_question  = None
        st.session_state.show_evaluation   = False
        st.session_state.evaluation        = None
        st.session_state.voice_transcript  = ""
        st.session_state.voice_recorded_q  = -1
        st.rerun()

    if end_btn:
        end_session(st.session_state.session_id)
        reset_interview_state()
        st.session_state.page = "results"
        st.rerun()

# ─── Evaluation Result ────────────────────────────────────────────────────────
def render_evaluation():
    ev       = st.session_state.evaluation
    cfg      = st.session_state.interview_config
    q_num    = st.session_state.question_num
    num_q    = cfg["num_questions"]
    score    = ev["score"]
    sc_color = get_score_color(score)

    # Score header
    st.markdown(f"""
    <div style="text-align:center;padding:1.5rem 0 0.5rem">
        <div style="font-size:3.5rem;font-weight:900;color:{sc_color}">
            {score}<span style="font-size:1.5rem;color:#64748b">/10</span>
        </div>
        <div style="font-size:1.2rem;font-weight:700;color:#e2e8f0;margin-top:0.3rem">
            {ev['verdict']}
        </div>
    </div>""", unsafe_allow_html=True)

    render_progress(q_num + 1, num_q)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Question & answer recap
    with st.expander("📋 View Question", expanded=False):
        st.markdown(f"_{ev.get('question', '')}_ ")
    with st.expander("💬 Your Answer", expanded=False):
        source = "🎤 Voice" if st.session_state.get("voice_recorded_q") == q_num - 1 else "⌨️ Typed"
        st.caption(source)
        st.markdown(ev.get("user_answer", ""))

    # Feedback tabs
    t1, t2, t3, t4 = st.tabs(["📊 Feedback", "✅ Model Answer", "🔧 Improvements", "📌 Concepts"])

    with t1:
        st.markdown(f"""
        <div style="background:#1a2035;border-radius:12px;padding:1rem;margin-bottom:1rem;
                    color:#e2e8f0;line-height:1.7">
            {ev.get('feedback', '')}
        </div>""", unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            if ev.get("strengths"):
                st.markdown("**💪 Strengths**")
                for s in ev["strengths"]:
                    st.markdown(f'<div class="feedback-strength">✅ {s}</div>', unsafe_allow_html=True)
        with cb:
            if ev.get("weaknesses"):
                st.markdown("**⚠️ Weaknesses**")
                for w in ev["weaknesses"]:
                    st.markdown(f'<div class="feedback-weakness">❌ {w}</div>', unsafe_allow_html=True)

    with t2:
        st.markdown("**🎯 Ideal answer a top candidate would give:**")
        st.markdown(f'<div class="feedback-model"><div style="color:#93c5fd;line-height:1.7">{ev.get("model_answer","")}</div></div>',
                    unsafe_allow_html=True)
        if ev.get("correct_answer"):
            st.markdown("**💡 Key insight:**")
            st.info(ev["correct_answer"])

    with t3:
        if ev.get("improvements"):
            st.markdown("**🚀 How to improve:**")
            for i, tip in enumerate(ev["improvements"], 1):
                st.markdown(f'<div class="feedback-tip"><strong style="color:#a78bfa">{i}.</strong> <span style="color:#e2e8f0">{tip}</span></div>',
                            unsafe_allow_html=True)

    with t4:
        ca, cb = st.columns(2)
        with ca:
            covered = ev.get("key_concepts_covered", [])
            if covered:
                st.markdown("**✅ Concepts Covered**")
                for c in covered:
                    st.markdown(f'<span class="company-badge" style="background:#052e16;border-color:#16a34a;color:#6ee7b7">✓ {c}</span>',
                                unsafe_allow_html=True)
        with cb:
            missed = ev.get("key_concepts_missed", [])
            if missed:
                st.markdown("**❌ Concepts Missed**")
                for m in missed:
                    st.markdown(f'<span class="company-badge" style="background:#450a0a;border-color:#dc2626;color:#fca5a5">✗ {m}</span>',
                                unsafe_allow_html=True)

    # Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    nb1, nb2 = st.columns(2)
    with nb1:
        next_label = "▶ Next Question" if q_num + 1 < num_q else "🏁 Finish & See Results"
        if st.button(next_label, use_container_width=True, key="next_q"):
            st.session_state.question_num     += 1
            st.session_state.current_question  = None
            st.session_state.show_evaluation   = False
            st.session_state.evaluation        = None
            if q_num + 1 >= num_q:
                end_session(st.session_state.session_id)
                st.session_state.interview_active = False
                st.session_state.page = "results"
            st.rerun()
    with nb2:
        if st.button("🔴 End Session Early", use_container_width=True, key="end_early"):
            end_session(st.session_state.session_id)
            reset_interview_state()
            st.session_state.page = "results"
            st.rerun()

# ─── Results ──────────────────────────────────────────────────────────────────
def render_results():
    answers = st.session_state.answers_list
    cfg     = st.session_state.interview_config

    if not answers:
        st.warning("No answers recorded in this session.")
        if st.button("Return to Dashboard"):
            st.session_state.page = "home"
            st.rerun()
        return

    scores = [a.get("score", 0) for a in answers]
    avg    = sum(scores) / len(scores)
    sc_col = get_score_color(avg)

    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0">
        <div style="font-size:4rem">🎉</div>
        <h1 style="font-size:2rem;color:#e2e8f0;margin:0.5rem 0">Session Complete!</h1>
        <div style="font-size:3rem;font-weight:900;color:{sc_col}">
            {avg:.1f}<span style="font-size:1.3rem;color:#64748b">/10</span>
        </div>
        <div style="color:#94a3b8">{len(answers)} questions &nbsp;·&nbsp;
            {cfg.get('role','')} &nbsp;·&nbsp; {cfg.get('domain','')}
        </div>
    </div>""", unsafe_allow_html=True)

    # Score bar chart
    fig = go.Figure(go.Bar(
        x=[f"Q{i+1}" for i in range(len(scores))],
        y=scores,
        marker_color=[get_score_color(s) for s in scores],
        text=scores, textposition="outside",
    ))
    fig.update_layout(
        height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        yaxis=dict(range=[0,11], gridcolor="rgba(99,102,241,0.1)"),
        xaxis=dict(gridcolor="rgba(99,102,241,0.1)"),
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)

    # AI summary
    with st.spinner("Generating AI performance summary…"):
        summary = generate_session_summary(
            answers=answers, role=cfg.get("role",""),
            domain=cfg.get("domain",""), company=cfg.get("company","General"),
        )
    st.markdown(f"""
    <div class="card">
        <h4 style="color:#a5b4fc;margin-top:0">🧠 AI Performance Summary</h4>
        <div style="color:#e2e8f0;line-height:1.7">{summary}</div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_interview_state()
            st.session_state.page = "setup"
            st.rerun()
    with c2:
        if st.button("📊 View Analytics", use_container_width=True):
            reset_interview_state()
            st.session_state.page = "analytics"
            st.rerun()

# ─── Analytics ────────────────────────────────────────────────────────────────
def render_analytics():
    user     = st.session_state.user
    sessions = get_user_sessions(user["id"])
    stats    = get_user_stats(user["id"])

    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#e2e8f0">📊 Performance Analytics</h1><hr>',
                unsafe_allow_html=True)

    if not sessions:
        st.markdown('<div class="alert-info" style="text-align:center;padding:3rem"><div style="font-size:2.5rem">📈</div><h3 style="color:#93c5fd">No data yet</h3><p>Complete your first interview to see analytics here!</p></div>',
                    unsafe_allow_html=True)
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sessions", stats.get("total_sessions") or 0)
    c2.metric("Avg Score",      f"{(stats.get('overall_avg') or 0):.1f}/10")
    c3.metric("Best Score",     f"{(stats.get('best_score')  or 0):.1f}/10")
    c4.metric("Questions Done", stats.get("total_questions") or 0)

    completed = [s for s in sessions if s["status"] == "completed"]
    if not completed:
        st.info("Complete a session to see detailed analytics.")
        return

    tab1, tab2 = st.tabs(["📈 Progress", "📋 Session History"])

    with tab1:
        df = pd.DataFrame(completed)
        df["date"] = pd.to_datetime(df["started_at"]).dt.strftime("%b %d")
        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(df, x="date", y="avg_score", markers=True,
                          title="Score Over Time",
                          color_discrete_sequence=["#6366f1"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#94a3b8"), height=300,
                              yaxis=dict(range=[0,10]),
                              title_font=dict(color="#e2e8f0"))
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            ds = df.groupby("domain")["avg_score"].mean().reset_index()
            fig2 = px.bar(ds, x="domain", y="avg_score",
                          title="Avg Score by Domain",
                          color_discrete_sequence=["#8b5cf6"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",
                               font=dict(color="#94a3b8"), height=300,
                               yaxis=dict(range=[0,10]),
                               title_font=dict(color="#e2e8f0"))
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        for s in completed[:10]:
            sc = s.get("avg_score") or 0
            with st.expander(
                f"{s['role']} — {s['domain']} | "
                f"Score: {sc:.1f}/10 | {s['started_at'][:10]}"
            ):
                for idx, a in enumerate(get_session_answers(s["id"]), 1):
                    asc = a.get("score") or 0
                    st.markdown(f"""
                    <div class="card">
                        <div style="display:flex;justify-content:space-between">
                            <strong style="color:#a5b4fc">Q{idx}: {a['question'][:80]}…</strong>
                            <span style="color:{get_score_color(asc)};font-weight:700">{asc}/10</span>
                        </div>
                        <div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem">
                            {(a.get('feedback') or '')[:150]}
                        </div>
                    </div>""", unsafe_allow_html=True)

# ─── Resume ───────────────────────────────────────────────────────────────────
def render_resume():
    st.markdown("""
    <h1 style="font-size:2rem;font-weight:800;color:#e2e8f0">📄 Resume Upload</h1>
    <p style="color:#64748b">Upload your resume to receive personalised interview questions</p><hr>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""
        <div class="alert-info" style="margin-bottom:1rem">
            <strong>Supported formats:</strong> PDF, DOCX, TXT<br>
            <strong>What we extract:</strong> Skills, experience level, education<br>
            <strong>How it helps:</strong> Questions tailored to YOUR background
        </div>""", unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Upload your resume",
            type=["pdf", "docx", "doc", "txt"],
            help="Max 5 MB. We only extract text — file is not stored.",
        )

        if uploaded:
            with st.spinner("Parsing resume…"):
                file_bytes = uploaded.read()
                if len(file_bytes) == 0:
                    st.error("❌ Uploaded file is empty. Please try again.")
                else:
                    parsed = parse_resume(file_bytes, uploaded.name)
                    if "error" in parsed:
                        st.error(f"❌ {parsed['error']}")
                    else:
                        st.session_state.resume_data = parsed
                        st.success(f"✅ Resume parsed! Found {len(parsed.get('skills', []))} skills.")

    with col2:
        rd = st.session_state.resume_data
        if rd:
            st.markdown("#### 📋 Extracted Information")
            st.markdown(f"**👤 Name detected:** {rd.get('name', 'N/A')}")

            if rd.get("skills"):
                st.markdown("**🛠️ Skills**")
                badges = "".join(f'<span class="company-badge">{s}</span>'
                                  for s in rd["skills"])
                st.markdown(badges, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            ca, cb = st.columns(2)
            ca.metric("Experience", f"{rd.get('experience_years','?')} yr(s)")
            cb.metric("Education",
                      rd["education"][0] if rd.get("education") else "N/A")

            st.markdown(f"""
            <div class="alert-success" style="margin-top:1rem;font-size:0.85rem">
                📊 Parsed {rd.get('char_count',0):,} characters from your resume.
            </div>""", unsafe_allow_html=True)

            if st.button("🗑️ Remove Resume", use_container_width=True):
                st.session_state.resume_data = None
                st.rerun()
        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:2rem;color:#64748b">
                <div style="font-size:2.5rem">📄</div>
                <div style="margin-top:0.5rem">Upload a resume on the left to see extracted info here</div>
            </div>""", unsafe_allow_html=True)

# ─── Settings ─────────────────────────────────────────────────────────────────
def render_settings():
    st.markdown('<h1 style="font-size:2rem;font-weight:800;color:#e2e8f0">⚙️ Settings</h1><hr>',
                unsafe_allow_html=True)

    st.markdown("#### 🔑 Groq API Key")
    current_key = os.getenv("GROQ_API_KEY", "")
    masked = ("●" * 20 + current_key[-6:]) if len(current_key) > 6 else "Not set"
    st.markdown(f'<div class="alert-info" style="margin-bottom:1rem">Current key: <code>{masked}</code></div>',
                unsafe_allow_html=True)

    new_key = st.text_input("Update API Key", type="password", placeholder="gsk_...")
    if st.button("💾 Save API Key") and new_key.strip():
        env_path = ".env"
        lines, found = [], False
        if os.path.exists(env_path):
            lines = open(env_path).readlines()
            for i, line in enumerate(lines):
                if line.startswith("GROQ_API_KEY"):
                    lines[i] = f"GROQ_API_KEY={new_key.strip()}\n"
                    found = True
        if not found:
            lines.append(f"GROQ_API_KEY={new_key.strip()}\n")
        open(env_path, "w").writelines(lines)
        os.environ["GROQ_API_KEY"] = new_key.strip()
        st.success("✅ API Key saved! Restart the app for it to fully take effect.")

    st.markdown("#### 📦 Dependencies Check")
    pkgs = {
        "groq": "Groq AI",
        "streamlit_mic_recorder": "Voice Input",
        "PyPDF2": "PDF Resume Parsing",
        "docx": "DOCX Resume Parsing",
        "bcrypt": "Auth Security",
        "plotly": "Analytics Charts",
    }
    ca, cb = st.columns(2)
    for i, (pkg, label) in enumerate(pkgs.items()):
        col = ca if i % 2 == 0 else cb
        try:
            __import__(pkg)
            col.markdown(f'<div class="alert-success" style="padding:0.5rem 1rem;margin:0.3rem 0">✅ {label}</div>',
                         unsafe_allow_html=True)
        except ImportError:
            col.markdown(f'<div class="alert-error" style="padding:0.5rem 1rem;margin:0.3rem 0">❌ {label} — pip install {pkg}</div>',
                         unsafe_allow_html=True)

    st.markdown("#### ℹ️ About")
    st.markdown("""
    <div class="card">
        <div style="color:#94a3b8;line-height:2">
            <strong style="color:#a5b4fc">AI Interview Coach v3.0</strong><br>
            Built by <strong>D. Satish</strong> · Enrollment: 23STUCHH010519<br>
            ICFAI Foundation for Higher Education, Hyderabad<br><br>
            <span style="color:#6366f1">Groq</span> LLaMA-3.3-70B &nbsp;·&nbsp;
            <span style="color:#6366f1">Groq</span> Whisper (Voice) &nbsp;·&nbsp;
            Streamlit &nbsp;·&nbsp; SQLite &nbsp;·&nbsp; Python
        </div>
    </div>""", unsafe_allow_html=True)

# ─── Router ───────────────────────────────────────────────────────────────────
def main():
    if not st.session_state.logged_in:
        render_auth()
        return

    render_sidebar()
    page = st.session_state.page

    # Guard active interview
    if st.session_state.interview_active and page not in ("interview", "results"):
        st.warning("⚠️ You have an active interview. Please complete or end it first.")
        if st.button("↩ Return to Interview"):
            st.session_state.page = "interview"
            st.rerun()
        return

    dispatch = {
        "home":      render_home,
        "setup":     render_setup,
        "interview": render_interview,
        "results":   render_results,
        "analytics": render_analytics,
        "resume":    render_resume,
        "settings":  render_settings,
    }
    dispatch.get(page, render_home)()

if __name__ == "__main__":
    main()
