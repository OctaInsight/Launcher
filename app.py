"""
Octa Platform — Central Launcher
Deploy as a standalone Streamlit app.
Single sign-on: login once, access all apps without re-entering credentials.
Session survives browser refresh. Auto-logout after 4 hours of inactivity.
"""
import streamlit as st
from modules.database import db
from modules.auth import (get_user_by_email, verify_password, set_session,
                          is_authenticated, _update_last_login, register_user,
                          request_password_reset, needs_password_change,
                          clear_session)
from modules.database import get_all_partners
from modules.sso import (create_session_token, auto_login_from_url,
                         set_token_in_url, logout, get_token_from_url)

st.set_page_config(
    page_title="Octa-CloudEARTHi Platform",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

DARK = {
    "bg":      "#0f1421",
    "bg2":     "#1a2235",
    "bg3":     "#232f45",
    "border":  "rgba(255,255,255,0.09)",
    "text":    "#e2e8f0",
    "muted":   "#8899b0",
    "accent":  "#00BCD4",
    "sidebar": "#1B2A4A",
    "success": "#28a745",
    "warning": "#f6ad55",
    "no_acc":  "#6b7280",
}

st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="block-container"] {{
    background-color: {DARK['bg']} !important;
    color: {DARK['text']} !important;
}}
[data-testid="stSidebarNav"],
[data-testid="stSidebar"] {{ display: none !important; }}
input {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    border-radius: 8px !important;
    color: {DARK['text']} !important;
}}
[data-testid="stButton"] > button {{
    background: {DARK['bg3']} !important;
    border: 1px solid {DARK['border']} !important;
    color: {DARK['text']} !important;
    border-radius: 8px !important;
}}
[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg,{DARK['accent']},#0097A7) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
}}
[data-testid="stButton"] > button:disabled {{
    opacity: 0.45 !important;
    cursor: not-allowed !important;
}}
</style>
""", unsafe_allow_html=True)

# ── App registry ──────────────────────────────────────────────────────────────
# status: "live" | "construction"
# columns: 1–5 (see layout below)
# col_order: position within that column

COLUMNS = {
    1: "🤝 Partner & Network",
    2: "📋 Proposal Suite",
    3: "🏗️ Project Management",
    4: "⏱️ People & Tasks",
    5: "📅 Calendar",
}

APPS = [
    # ── Column 1: Partner & Network ────────────────────────────────────────────
    {
        "key":         "octa_partners",
        "label":       "Partner Network",
        "icon":        "🌐",
        "description": "Partner profiles, contacts, CloudEARTHi Alliance members",
        "url":         "https://octa-partners.streamlit.app/",   # ← your real URL
        "status":      "live",                                      # ← change this
        "col":         1,
    },
    {
        "key":         "octa_social",
        "label":       "Social Media Hub",
        "icon":        "📱",
        "description": "Create & publish content, tag partners across all channels",
        "url":         "",
        "status":      "construction",
        "col":         1,
    },
    {
        "key":         "octa_communication",
        "label":       "Partner Communication",
        "icon":        "📧",
        "description": "Centralised partner messaging and outreach across projects",
        "url":         "",
        "status":      "construction",
        "col":         1,
    },
    # ── Column 2: Proposal Suite ───────────────────────────────────────────────
    {
        "key":         "octa_proposals",
        "label":       "Proposal Tracker",
        "icon":        "📋",
        "description": "Track proposals, budgets, deadlines, PES fund & partners",
        "url":         "https://proposal-progress.streamlit.app",
        "status":      "live",
        "col":         2,
    },
    {
        "key":         "octa_intelligence",
        "label":       "Proposal Intelligence",
        "icon":        "🤖",
        "description": "AI-powered call analysis, strategy & positioning suggestions",
        "url":         "",
        "status":      "construction",
        "col":         2,
    },
    {
        "key":         "octa_kpi",
        "label":       "Objectives & Work Plan Designer",
        "icon":        "📊",
        "description": "Design KPIs, deliverables, work packages, Gantt & budget",
        "url":         "https://octakpi.streamlit.app/",
        "status":      "live",
        "col":         2,
    },
    {
        "key":         "octa_writer",
        "label":       "Proposal Writing Studio",
        "icon":        "📝",
        "description": "Collaborative writing with AI assistance and version history",
        "url":         "",
        "status":      "construction",
        "col":         2,
    },
    {
        "key":         "octa_review",
        "label":       "Review & Evaluation",
        "icon":        "🔍",
        "description": "Internal review, scoring and quality control before submission",
        "url":         "",
        "status":      "construction",
        "col":         2,
    },
    # ── Column 3: Project Management ───────────────────────────────────────────
    {
        "key":         "octa_projects",
        "label":       "Project Progress Tracker",
        "icon":        "🏗️",
        "description": "Monitor funded project milestones, deadlines and deliverables",
        "url":         "",
        "status":      "construction",
        "col":         3,
    },
    {
        "key":         "octa_implementation",
        "label":       "Implementation Monitor",
        "icon":        "⚙️",
        "description": "Activity-level tracking, partner contributions and reporting",
        "url":         "",
        "status":      "construction",
        "col":         3,
    },
    {
        "key":         "octa_financial",
        "label":       "Financial Control",
        "icon":        "💶",
        "description": "Budget consumption, forecasting and financial reporting",
        "url":         "",
        "status":      "construction",
        "col":         3,
    },
    # ── Column 4: People & Tasks ────────────────────────────────────────────────
    {
        "key":         "octa_hours",
        "label":       "Working Hours",
        "icon":        "⏱️",
        "description": "Log, approve and report working hours per proposal or project",
        "url":         "https://working-hours.streamlit.app",
        "status":      "live",
        "col":         4,
    },
    {
        "key":         "octa_tasks",
        "label":       "Task Manager",
        "icon":        "✅",
        "description": "Assign tasks, track progress and manage team to-dos",
        "url":         "",
        "status":      "construction",
        "col":         4,
    },
    # ── Column 5: Calendar (full-height) ────────────────────────────────────────
    {
        "key":         "octa_calendar",
        "label":       "Common Calendar",
        "icon":        "📅",
        "description": "Unified calendar: deadlines, meetings, milestones & events across all apps",
        "url":         "",
        "status":      "construction",
        "col":         5,
    },
]

# ── Try SSO auto-login from URL token ─────────────────────────────────────────
auto_login_from_url()

# ═════════════════════════════════════════════════════════════════════════════
# LOGIN SCREEN — 3 tabs: Sign In | Register | Forgot Password
# ═════════════════════════════════════════════════════════════════════════════
if not is_authenticated():
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(f"""
<div style="text-align:center;padding:2.5rem 0 1.5rem">
<div style="font-size:4rem">🚀</div>
<h1 style="color:white;font-size:2.2rem;font-weight:800;
           margin:0.5rem 0 0.2rem;letter-spacing:-1px">Octa Platform</h1>
<p style="color:{DARK['muted']};font-size:0.95rem;margin:0">
Sign in once — access all your apps</p>
</div>""", unsafe_allow_html=True)

        tab_login, tab_reg, tab_reset = st.tabs(
            ["🔑  Sign In", "✨  Register", "🔓  Forgot Password"]
        )

        # ── Sign In ───────────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            email    = st.text_input("Email address", placeholder="you@example.com",
                                      key="l_email")
            password = st.text_input("Password", type="password", key="l_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In → Access All Apps", type="primary",
                         use_container_width=True, key="btn_login"):
                if not email or not password:
                    st.warning("Please fill in both fields.")
                else:
                    user = get_user_by_email(email)
                    if not user:
                        st.error("❌ No account found with this email.")
                    elif user.get("status") == "pending":
                        st.error("⏳ Your account is pending admin approval.")
                    elif user.get("status") == "disabled":
                        st.error("🚫 Account disabled. Contact your admin.")
                    elif not verify_password(password, user.get("password_hash","")):
                        st.error("❌ Incorrect password.")
                    else:
                        set_session(user)
                        _update_last_login(user["id"])
                        token = create_session_token(user["id"])
                        if token:
                            st.session_state["sso_token"] = token
                            set_token_in_url(token)
                        st.rerun()

        # ── Register ──────────────────────────────────────────────────────────
        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            muted_c = DARK["muted"]; acc_c = DARK["accent"]; txt_c = DARK["text"]
            st.markdown(
                f"<div style='background:rgba(0,188,212,0.1);border:1px solid rgba(0,188,212,0.3);"
                f"border-left:4px solid {acc_c};border-radius:10px;"
                f"padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.88rem'>"
                f"<strong style='color:{acc_c}'>How it works</strong><br>"
                f"<span style='color:{txt_c}'>1. Fill in the form and submit<br>"
                f"2. An admin reviews and activates your account<br>"
                f"3. Come back to Sign In once notified</span></div>",
                unsafe_allow_html=True
            )
            rc1,rc2 = st.columns(2)
            with rc1: reg_first = st.text_input("First name *", key="reg_first", placeholder="Maria")
            with rc2: reg_last  = st.text_input("Last name *",  key="reg_last",  placeholder="Rossi")
            reg_uname = st.text_input("Username *", key="reg_uname", placeholder="mariarossi (min 3 chars)")
            reg_email = st.text_input("Email *",    key="reg_email", placeholder="you@example.com")

            OTHER_ORG = "➕  My organisation is not in the list"
            try:
                pnames = [p["full_name"] for p in get_all_partners() if p.get("full_name")]
            except Exception:
                pnames = []
            org_opts = ["— Select your organisation —"] + sorted(pnames) + [OTHER_ORG]
            reg_org_sel = st.selectbox("Organisation *", options=org_opts, key="reg_org_sel")
            reg_org_custom = ""
            if reg_org_sel == OTHER_ORG:
                reg_org_custom = st.text_input("Enter organisation name *", key="reg_org_cust",
                                               placeholder="Full name of your organisation")
            def _org():
                if reg_org_sel == OTHER_ORG: return reg_org_custom.strip()
                if reg_org_sel.startswith("—"): return ""
                return reg_org_sel

            rc3,rc4 = st.columns(2)
            with rc3: reg_pass  = st.text_input("Password *", type="password", key="reg_pass",  placeholder="Min 8 chars")
            with rc4: reg_pass2 = st.text_input("Confirm *",  type="password", key="reg_pass2", placeholder="Repeat password")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Submit Registration →", type="primary",
                         use_container_width=True, key="btn_reg"):
                org_val = _org()
                if reg_pass != reg_pass2:
                    st.error("❌ Passwords do not match.")
                elif not all([reg_first,reg_last,reg_uname,reg_email,reg_pass]):
                    st.warning("Please fill in all required fields.")
                elif reg_org_sel.startswith("—"):
                    st.warning("Please select your organisation.")
                elif reg_org_sel == OTHER_ORG and not reg_org_custom.strip():
                    st.warning("Please enter your organisation name.")
                else:
                    ok,msg,_ = register_user(reg_email,reg_uname,reg_first,
                                             reg_last,reg_pass,organisation=org_val)
                    if ok:
                        suc_c = DARK["success"]
                        st.markdown(
                            f"<div style='background:rgba(40,167,69,0.12);"
                            f"border-left:4px solid {suc_c};border-radius:10px;"
                            f"padding:1rem 1.2rem;margin-top:1rem'>"
                            f"✅ <strong style='color:{suc_c}'>Registration submitted!</strong><br>"
                            f"<span style='color:{txt_c};font-size:0.88rem'>"
                            f"Organisation: <strong>{org_val or '—'}</strong><br>"
                            f"Your account is <strong>pending admin approval</strong>."
                            f"</span></div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.error(f"❌ {msg}")

        # ── Forgot Password ───────────────────────────────────────────────────
        with tab_reset:
            st.markdown("<br>", unsafe_allow_html=True)
            warn_c = DARK["warning"]; txt_c = DARK["text"]
            st.markdown(
                f"<div style='background:rgba(246,204,82,0.1);border:1px solid rgba(246,204,82,0.3);"
                f"border-left:4px solid {warn_c};border-radius:10px;"
                f"padding:0.9rem 1.1rem;margin-bottom:1rem;font-size:0.88rem'>"
                f"<strong style='color:{warn_c}'>Secure password reset</strong><br>"
                f"<span style='color:{txt_c}'>1. Submit your email below<br>"
                f"2. An admin verifies your identity and generates a temporary password<br>"
                f"3. The admin shares it with you directly (phone / personal email)<br>"
                f"4. Log in with the temporary password and set a new one</span></div>",
                unsafe_allow_html=True
            )
            fp_email = st.text_input("Your registered email", key="fp_email",
                                      placeholder="you@example.com")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Submit Reset Request →", type="primary",
                         use_container_width=True, key="btn_reset"):
                if not fp_email.strip():
                    st.warning("Please enter your email address.")
                else:
                    ok,msg = request_password_reset(fp_email.strip())
                    if ok: st.success(f"✅ {msg}")
                    else:  st.error(f"❌ {msg}")

        muted_c = DARK["muted"]
        st.markdown(
            f"<div style='text-align:center;margin-top:1rem;color:{muted_c};font-size:0.75rem'>"
            f"Octa Platform · Questions? octainsight@gmail.com</div>",
            unsafe_allow_html=True
        )
    st.stop()

# ═════════════════════════════════════════════════════════════════════════════
# LAUNCHER DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
uname     = st.session_state.get("first_name") or st.session_state.get("username","")
org       = st.session_state.get("organisation","")
role      = st.session_state.get("role","user")
user_apps = set(st.session_state.get("apps_access",[]))
token     = st.session_state.get("sso_token","") or get_token_from_url()

if token:
    set_token_in_url(token)

# ── Header ────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([5, 1])
with hc1:
    st.markdown(f"""
    <div style="padding:1.2rem 0 0.8rem">
        <h1 style="color:white;font-size:1.9rem;font-weight:800;margin:0">
            🚀 Octa Platform
        </h1>
        <p style="color:{DARK['muted']};margin:0.2rem 0 0;font-size:0.9rem">
            Welcome, <strong style="color:{DARK['text']}">{uname}</strong>
            {(' · ' + org) if org else ''}
            {' · 🛡️ Admin' if role == 'admin' else ''}
            &nbsp;·&nbsp; Session expires after 4h of inactivity
        </p>
    </div>
    """, unsafe_allow_html=True)
with hc2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True, key="btn_signout"):
        logout()
        st.rerun()

# ── Legend ────────────────────────────────────────────────────────────────────
acc_c  = DARK["success"]    # green
no_c   = DARK["no_acc"]     # gray
con_c  = DARK["warning"]    # amber

st.markdown(f"""
<div style="display:flex;gap:2rem;flex-wrap:wrap;margin-bottom:1.5rem;
            padding:0.6rem 1rem;background:{DARK['bg2']};border-radius:8px;
            border:1px solid {DARK['border']};font-size:0.82rem">
    <span>
        <span style="display:inline-block;width:11px;height:11px;
                     background:{acc_c};border-radius:50%;margin-right:5px;
                     vertical-align:middle"></span>
        <strong style="color:{acc_c}">You have access</strong> — click to open
    </span>
    <span>
        <span style="display:inline-block;width:11px;height:11px;
                     background:{no_c};border-radius:50%;margin-right:5px;
                     vertical-align:middle"></span>
        <strong style="color:{no_c}">No access</strong> — contact admin
    </span>
    <span>
        <span style="display:inline-block;width:11px;height:11px;
                     background:{con_c};border-radius:50%;margin-right:5px;
                     vertical-align:middle"></span>
        <strong style="color:{con_c}">Under construction</strong> — coming soon
    </span>
</div>
""", unsafe_allow_html=True)

# ── Build 5 columns ───────────────────────────────────────────────────────────
cols = st.columns([1.1, 1.3, 1.1, 1, 0.9])

# Group apps by column
from collections import defaultdict
by_col = defaultdict(list)
for app in APPS:
    by_col[app["col"]].append(app)

def _render_app_card(app, token, user_apps, role, acc_c, no_c, con_c, DARK):
    app_key = app["key"]
    status  = app["status"]
    has_acc = (app_key in user_apps) or (role == "admin")
    url     = app.get("url","")

    if status == "construction":
        border = con_c
        bg     = "rgba(246,173,85,0.08)"
        badge  = "🚧 Under construction"
        badge_color = con_c
        clickable   = False
    elif has_acc:
        border = acc_c
        bg     = "rgba(40,167,69,0.1)"
        badge  = "✓ Open"
        badge_color = acc_c
        clickable   = True
    else:
        border = no_c
        bg     = "rgba(107,114,128,0.06)"
        badge  = "🔒 No access"
        badge_color = no_c
        clickable   = False

    opacity = "1" if clickable else "0.6"
    muted   = DARK["muted"]
    txt     = DARK["text"]

    st.markdown(f"""
<div style="background:{bg};border:1px solid {border}55;
            border-top:3px solid {border};border-radius:12px;
            padding:1rem 1rem 0.8rem;margin-bottom:0.8rem;
            min-height:130px;opacity:{opacity}">
    <div style="font-size:1.6rem;margin-bottom:0.3rem">{app['icon']}</div>
    <div style="font-size:0.88rem;font-weight:700;color:{txt};
                margin-bottom:0.25rem;line-height:1.3">{app['label']}</div>
    <div style="font-size:0.74rem;color:{muted};margin-bottom:0.6rem;
                line-height:1.35">{app['description']}</div>
    <span style="background:{badge_color}22;color:{badge_color};
                 border:1px solid {badge_color}44;padding:2px 8px;
                 border-radius:12px;font-size:0.7rem;font-weight:600">
        {badge}
    </span>
</div>
""", unsafe_allow_html=True)

    if clickable and url:
        sso_url = f"{url}/?session={token}" if token else url
        st.link_button("Open →", url=sso_url, use_container_width=True)
    else:
        st.button(
            "🔒 No access" if (status == "live" and not has_acc) else "🚧 Coming soon",
            key=f"dis_{app_key}",
            disabled=True,
            use_container_width=True,
        )


for col_num, col_widget in enumerate(cols, start=1):
    with col_widget:
        col_label = COLUMNS.get(col_num,"")
        muted = DARK["muted"]
        st.markdown(
            f"<div style='font-size:0.72rem;font-weight:600;letter-spacing:0.08em;"
            f"text-transform:uppercase;color:{muted};margin-bottom:0.7rem;"
            f"padding-bottom:0.3rem;border-bottom:1px solid rgba(255,255,255,0.1)'>"
            f"{col_label}</div>",
            unsafe_allow_html=True
        )

        for app in by_col[col_num]:
            # Calendar (col 5) gets a special large card
            if col_num == 5:
                app_key = app["key"]
                status  = app["status"]
                has_acc = (app_key in user_apps) or (role == "admin")
                url     = app.get("url","")
                border  = acc_c if (status == "live" and has_acc) else con_c
                bg      = "rgba(40,167,69,0.1)" if (status=="live" and has_acc) \
                          else "rgba(246,173,85,0.08)"
                badge   = "✓ Open" if (status=="live" and has_acc) else "🚧 Coming soon"
                badge_c = acc_c   if (status=="live" and has_acc) else con_c
                muted   = DARK["muted"]
                txt     = DARK["text"]

                st.markdown(f"""
<div style="background:{bg};border:1px solid {border}55;
            border-top:4px solid {border};border-radius:14px;
            padding:2rem 1.2rem;text-align:center;min-height:340px;
            display:flex;flex-direction:column;justify-content:center;
            align-items:center">
    <div style="font-size:3.5rem;margin-bottom:0.8rem">{app['icon']}</div>
    <div style="font-size:1.1rem;font-weight:800;color:{txt};
                margin-bottom:0.6rem">{app['label']}</div>
    <div style="font-size:0.8rem;color:{muted};line-height:1.5;
                margin-bottom:1rem;max-width:160px">{app['description']}</div>
    <span style="background:{badge_c}22;color:{badge_c};
                 border:1px solid {badge_c}44;padding:3px 12px;
                 border-radius:14px;font-size:0.74rem;font-weight:600">
        {badge}
    </span>
</div>
""", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
            else:
                _render_app_card(app, token, user_apps, role,
                                 acc_c, no_c, con_c, DARK)
