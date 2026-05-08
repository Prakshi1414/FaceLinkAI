import streamlit as st
import requests
import os
import zipfile
import io
from datetime import date, datetime
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG test
# ─────────────────────────────────────────────────────────────────────────────
API_BASE   = "http://127.0.0.1:8000"
IMAGE_BASE = f"{API_BASE}/images"

st.set_page_config(
    page_title="FaceLinkAI Studio",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none;}
:root{
  --navy:#0a1628;--navy2:#0f1e35;--blue:#1a6dff;--blue-l:#5b9dff;
  --blue-dim:rgba(26,109,255,.15);--blue-bd:rgba(26,109,255,.35);
  --green:#1d9e75;--red:#e24b4a;--amber:#ef9f27;
  --bg:#f0f4f9;--card:#ffffff;--border:rgba(0,0,0,.08);
  --t1:#0d1b2a;--t2:#5a6a7e;--t3:#96a3b1;
}
/* Navbar */
.fl-nav{background:var(--navy);padding:0 2rem;height:56px;display:flex;align-items:center;
  justify-content:space-between;position:sticky;top:0;z-index:999;}
.fl-logo{display:flex;align-items:center;gap:10px;}
.fl-logo-icon{width:34px;height:34px;background:var(--blue);border-radius:8px;
  display:flex;align-items:center;justify-content:center;font-size:16px;}
.fl-logo-text{font-size:17px;font-weight:600;color:#fff;letter-spacing:-.3px;}
.fl-nav-right{display:flex;align-items:center;gap:14px;}
.fl-studio-name{font-size:13px;color:#8899bb;}
.fl-avatar{width:32px;height:32px;border-radius:50%;background:#1a4aaa;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:#fff;}
/* Page wrapper */
.fl-page{background:var(--bg);min-height:calc(100vh - 56px);padding:2rem 2.5rem;}
/* Auth */
.auth-left{background:var(--navy);padding:3rem;min-height:100vh;display:flex;flex-direction:column;justify-content:space-between;}
.auth-badge{display:inline-flex;align-items:center;gap:6px;background:var(--blue-dim);
  border:1px solid var(--blue-bd);border-radius:20px;padding:4px 12px;
  font-size:11px;color:var(--blue-l);margin-bottom:16px;}
.auth-badge-dot{width:6px;height:6px;border-radius:50%;background:var(--blue);display:inline-block;}
.auth-tagline h2{font-size:24px;font-weight:600;color:#fff;margin-bottom:10px;line-height:1.3;}
.auth-tagline p{font-size:14px;color:#8899bb;line-height:1.6;}
/* Cards */
.fl-card{background:var(--card);border:.5px solid var(--border);border-radius:14px;padding:1.5rem;margin-bottom:1rem;}
.fl-card-dark{background:var(--navy);border-radius:14px;padding:1.25rem 1.5rem;margin-bottom:1rem;}
/* Stat cards */
.stat-card{background:var(--card);border:.5px solid var(--border);border-radius:10px;padding:1rem 1.25rem;}
.stat-label{font-size:11px;color:var(--t2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;}
.stat-val{font-size:26px;font-weight:600;color:var(--t1);}
.stat-hint{font-size:11px;color:var(--t3);margin-top:2px;}
/* Album cards */
.album-card{background:var(--card);border:.5px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:.75rem;}
.album-thumb{height:110px;display:flex;align-items:center;justify-content:center;position:relative;}
.album-badge{position:absolute;top:8px;right:8px;background:rgba(0,0,0,.45);border-radius:20px;padding:3px 9px;font-size:11px;color:#fff;}
.share-pill{position:absolute;top:8px;left:8px;background:rgba(26,109,255,.82);border-radius:20px;padding:3px 9px;font-size:10px;color:#fff;}
.album-info{padding:12px 14px;}
.album-name{font-size:14px;font-weight:600;color:var(--t1);margin-bottom:3px;}
.album-meta{font-size:11px;color:var(--t2);}
.album-footer{display:flex;align-items:center;justify-content:space-between;margin-top:10px;
  padding-top:10px;border-top:.5px solid var(--border);}
.status-dot{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:5px;}
.chip{font-size:10px;background:#f0f4f9;border:.5px solid var(--border);border-radius:20px;padding:2px 8px;color:var(--t2);}
/* Photo grid */
.photo-item{border-radius:10px;overflow:hidden;margin-bottom:8px;position:relative;background:#0f1e35;}
.photo-person-tag{position:absolute;bottom:5px;left:5px;background:rgba(0,0,0,.6);
  border-radius:10px;padding:2px 7px;font-size:9px;color:#fff;}
/* Buttons */
.stButton>button{background:var(--blue)!important;color:#fff!important;border:none!important;
  border-radius:8px!important;font-size:13px!important;font-weight:500!important;
  padding:.45rem 1.2rem!important;transition:opacity .15s!important;}
.stButton>button:hover{opacity:.9!important;}
/* Alerts */
.fl-err{display:flex;align-items:center;gap:10px;background:#fff0f0;border:.5px solid #fca5a5;
  border-radius:8px;padding:10px 14px;margin-bottom:14px;}
.fl-err span{font-size:13px;color:#b91c1c;}
.fl-ok{display:flex;align-items:center;gap:10px;background:#f0fdf4;border:.5px solid #86efac;
  border-radius:8px;padding:10px 14px;margin-bottom:14px;}
.fl-ok span{font-size:13px;color:#15803d;}
.fl-info{display:flex;align-items:center;gap:10px;background:#eff6ff;border:.5px solid #93c5fd;
  border-radius:8px;padding:10px 14px;margin-bottom:14px;}
.fl-info span{font-size:13px;color:#1d4ed8;}
/* Upload zone */
.upload-zone{border:2px dashed #cbd5e1;border-radius:14px;padding:2rem;text-align:center;background:var(--card);margin-bottom:1rem;}
/* Section heading */
.fl-sh{font-size:16px;font-weight:600;color:var(--t1);margin-bottom:12px;margin-top:1.5rem;}
.fl-cb{font-size:11px;font-weight:400;color:var(--t3);background:#f0f4f9;border:.5px solid var(--border);border-radius:20px;padding:1px 8px;margin-left:8px;}
/* Match card */
.match-card{position:relative;border-radius:10px;overflow:hidden;border:2px solid var(--green);margin-bottom:8px;}
.match-ob{position:absolute;top:5px;right:5px;background:rgba(29,158,117,.9);border-radius:10px;padding:2px 7px;font-size:9px;color:#fff;font-weight:600;}
.match-cb{position:absolute;bottom:5px;left:5px;background:rgba(0,0,0,.6);border-radius:10px;padding:2px 7px;font-size:9px;color:#cef;}
/* Share link */
.share-link-box{background:#f8fafc;border:.5px solid #cbd5e1;border-radius:8px;padding:10px 14px;
  font-family:monospace;font-size:12px;color:var(--t1);word-break:break-all;margin-bottom:12px;}
/* Empty state */
.fl-empty{text-align:center;padding:3rem 2rem;color:var(--t2);}
.fl-empty-icon{font-size:48px;margin-bottom:12px;}
.fl-empty-title{font-size:16px;font-weight:600;color:var(--t1);margin-bottom:6px;}
.fl-empty-sub{font-size:13px;line-height:1.6;}
/* Steps */
.fl-steps{display:flex;align-items:center;gap:0;margin-bottom:1.5rem;flex-wrap:wrap;gap:4px;}
.fl-step{display:flex;align-items:center;gap:8px;}
.fl-step-num{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;}
.fl-step-num.active{background:var(--blue);color:#fff;}
.fl-step-num.done{background:var(--green);color:#fff;}
.fl-step-num.idle{background:#e2e8f0;color:var(--t2);}
.fl-step-label{font-size:12px;color:var(--t2);}
.fl-step.active .fl-step-label{color:var(--t1);font-weight:500;}
.fl-step-conn{width:24px;height:1px;background:#cbd5e1;margin:0 4px;}
/* Inputs */
.stTextInput>div>div>input,.stTextArea>div>div>textarea{border-radius:8px!important;border:.5px solid #cbd5e1!important;font-size:14px!important;}
.stTextInput>div>div>input:focus{border-color:var(--blue)!important;box-shadow:0 0 0 2px var(--blue-dim)!important;}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{gap:0;background:#f0f4f9;border-radius:8px;padding:3px;width:fit-content;}
.stTabs [data-baseweb="tab"]{border-radius:6px;padding:.35rem 1rem;font-size:13px;font-weight:500;color:var(--t2);}
.stTabs [aria-selected="true"]{background:var(--blue)!important;color:#fff!important;}
.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-baseweb="tab-panel"]{padding-top:1.5rem;}
/* Scrollbar */
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:3px;}
.stFileUploader>div{border-radius:10px!important;border:1.5px dashed #cbd5e1!important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = {
    "token": None,
    "user_id": None,
    "studio_name": None,
    "username": None,
    "page": "login",
    "selected_album": None,
    "share_link_pending": None,
    "recog_results": None,
    "recog_step": 1,
    "selfie_file": None,
    "create_album_open": False,
    "upload_results": None,
    "login_error": None,
    "reg_error": None,
    "reg_success": None,
    "cl_login_error": None,
    "cl_reg_error": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# URL QUERY PARAM — share link via ?share=<token>
# ─────────────────────────────────────────────────────────────────────────────
_params = st.query_params
if "share" in _params and not st.session_state.share_link_pending:
    st.session_state.share_link_pending = _params["share"]
    if not st.session_state.token:
        st.session_state.page = "client_login"


# ─────────────────────────────────────────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(endpoint, json=None, files=None, data=None, auth=False):
    headers = _auth_headers() if auth else {}
    try:
        r = requests.post(
            f"{API_BASE}{endpoint}",
            json=json, files=files, data=data,
            headers=headers, timeout=180,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_get(endpoint, auth=False, params=None):
    headers = _auth_headers() if auth else {}
    try:
        r = requests.get(
            f"{API_BASE}{endpoint}",
            headers=headers, params=params, timeout=30,
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def image_url(img_path: str) -> str:
    return f"{IMAGE_BASE}/{img_path}"


def fmt_size(b: int) -> str:
    if not b:
        return "0 B"
    if b < 1024:
        return f"{b} B"
    if b < 1024 ** 2:
        return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"


def fmt_date(d) -> str:
    if not d:
        return "—"
    try:
        s = d if isinstance(d, str) else str(d)
        return datetime.fromisoformat(s.split("T")[0]).strftime("%b %d, %Y")
    except Exception:
        return str(d)


def nav(page, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def logout():
    for k in ["token","user_id","studio_name","username","selected_album",
              "recog_results","recog_step","upload_results","selfie_file"]:
        st.session_state[k] = None
    st.session_state.page = "login"
    st.rerun()


def _extract_error(resp: dict) -> Optional[str]:
    if "error" in resp:
        return f"Connection error: {resp['error']}"
    detail = resp.get("detail", {})
    if isinstance(detail, dict) and detail.get("status") is False:
        return detail.get("message", "Something went wrong.")
    if resp.get("status") is False:
        return resp.get("message", "Something went wrong.")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# COMPONENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def alert_error(msg):
    st.markdown(f'<div class="fl-err"><span>⚠ {msg}</span></div>', unsafe_allow_html=True)

def alert_success(msg):
    st.markdown(f'<div class="fl-ok"><span>✓ {msg}</span></div>', unsafe_allow_html=True)

def alert_info(msg):
    st.markdown(f'<div class="fl-info"><span>ℹ {msg}</span></div>', unsafe_allow_html=True)


def render_navbar(show_back=False, back_label="← Albums", back_page="dashboard"):
    studio  = st.session_state.studio_name or "Studio"
    initials = "".join(w[0].upper() for w in studio.split()[:2])
    st.markdown(f"""
    <div class="fl-nav">
      <div class="fl-logo">
        <div class="fl-logo-icon">🔗</div>
        <span class="fl-logo-text">FaceLinkAI</span>
      </div>
      <div class="fl-nav-right">
        <span class="fl-studio-name">{studio}</span>
        <div class="fl-avatar">{initials}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if show_back:
        c1, _, c3 = st.columns([2, 7, 1])
        with c1:
            if st.button(back_label, key="nav_back_btn"):
                nav(back_page)
        with c3:
            if st.button("Logout", key="nav_logout_b"):
                logout()
    else:
        _, c3 = st.columns([11, 1])
        with c3:
            if st.button("Logout", key="nav_logout_m"):
                logout()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: LOGIN / REGISTER
# ─────────────────────────────────────────────────────────────────────────────
def page_login():
    left_col, right_col = st.columns([2, 3])

    with left_col:
        st.markdown("""
        <div class="auth-left">
          <div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:2.5rem">
              <div style="width:36px;height:36px;background:#1a6dff;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px">🔗</div>
              <span style="font-size:18px;font-weight:600;color:#fff">FaceLinkAI</span>
            </div>
          </div>
          <div>
            <div class="auth-badge"><span class="auth-badge-dot"></span> Studio Edition</div>
            <div class="auth-tagline">
              <h2>AI-powered photo recognition for photography studios</h2>
              <p>Automatically detect faces, link clients to their photos, and share albums in seconds.</p>
            </div>
          </div>
          <div style="font-size:11px;color:#445566">© 2025 FaceLinkAI. All rights reserved.</div>
        </div>
        """, unsafe_allow_html=True)

    with right_col:
        st.markdown("<div style='padding:3rem 2rem;min-height:100vh;background:#f0f4f9;display:flex;flex-direction:column;justify-content:center'>", unsafe_allow_html=True)

        tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])

        with tab_in:
            _login_form()

        with tab_reg:
            _register_form()

        st.markdown("</div>", unsafe_allow_html=True)


def _login_form():
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown("#### Welcome back")
    st.markdown("<p style='font-size:13px;color:#5a6a7e;margin-top:-6px;margin-bottom:1rem'>Sign in to your studio account</p>", unsafe_allow_html=True)

    if st.session_state.login_error:
        alert_error(st.session_state.login_error)
        st.session_state.login_error = None

    mobile   = st.text_input("Mobile Number", placeholder="10-digit mobile number", key="li_mob")
    password = st.text_input("Password", type="password", placeholder="Enter your password", key="li_pw")

    if st.button("Sign In", key="btn_signin", use_container_width=True):
        if not mobile or not password:
            alert_error("Please fill in all fields.")
        elif not mobile.isdigit() or len(mobile) != 10:
            alert_error("Mobile number must be exactly 10 digits.")
        else:
            with st.spinner("Signing in..."):
                resp = api_post("/login-user", json={"mobile_number": mobile, "password": password})
            err = _extract_error(resp)
            if err:
                st.session_state.login_error = err
                st.rerun()
            else:
                data = resp.get("data", resp)
                st.session_state.token       = data.get("access_token")
                st.session_state.user_id     = data.get("user_id")
                st.session_state.studio_name = data.get("studio_name")
                st.session_state.username    = data.get("username")
                if st.session_state.share_link_pending:
                    nav("client_gallery")
                else:
                    nav("dashboard")


def _register_form():
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown("#### Create your account")
    st.markdown("<p style='font-size:13px;color:#5a6a7e;margin-top:-6px;margin-bottom:1rem'>Set up your photography studio</p>", unsafe_allow_html=True)

    if st.session_state.reg_error:
        alert_error(st.session_state.reg_error)
        st.session_state.reg_error = None
    if st.session_state.reg_success:
        alert_success(st.session_state.reg_success)
        st.session_state.reg_success = None

    studio   = st.text_input("Studio Name", placeholder="e.g. Sharma Photography Studio", key="rg_studio")
    username = st.text_input("Username", placeholder="e.g. sharma_studio", key="rg_user")
    mob      = st.text_input("Mobile Number", placeholder="10-digit number", key="rg_mob")
    c1, c2   = st.columns(2)
    with c1:
        email = st.text_input("Email (optional)", placeholder="studio@email.com", key="rg_email")
    with c2:
        pw = st.text_input("Password", type="password", placeholder="Min 8 chars", key="rg_pw")
    cpw = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="rg_cpw")

    if st.button("Create Studio Account", key="btn_reg", use_container_width=True):
        errs = []
        if not studio:   errs.append("Studio name required.")
        if not username: errs.append("Username required.")
        if not mob or not mob.isdigit() or len(mob) != 10:
            errs.append("Mobile number must be 10 digits.")
        if not pw or len(pw) < 8:
            errs.append("Password min 8 characters.")
        if pw != cpw:    errs.append("Passwords do not match.")
        if errs:
            st.session_state.reg_error = " | ".join(errs)
            st.rerun()
        else:
            payload = {"studio_name": studio, "username": username,
                       "mobile_number": mob, "password": pw}
            if email:
                payload["email"] = email
            with st.spinner("Creating account..."):
                resp = api_post("/register-user", json=payload)
            err = _extract_error(resp)
            if err:
                st.session_state.reg_error = err
                st.rerun()
            else:
                st.session_state.reg_success = "Account created! Please sign in."
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CLIENT LOGIN (share link flow)
# ─────────────────────────────────────────────────────────────────────────────
def page_client_login():
    st.markdown("""
    <div class="fl-nav">
      <div class="fl-logo">
        <div class="fl-logo-icon">🔗</div>
        <span class="fl-logo-text">FaceLinkAI</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([2, 3, 2])
    with center:
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="fl-card-dark" style="display:flex;align-items:center;gap:14px">
          <div style="width:44px;height:44px;background:#1a3a7a;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">📷</div>
          <div>
            <div style="font-size:15px;font-weight:600;color:#fff">Shared Album</div>
            <div style="font-size:12px;color:#8899bb;margin-top:3px">Login required to view photos</div>
          </div>
          <div style="margin-left:auto;background:rgba(26,109,255,.2);border:.5px solid rgba(26,109,255,.4);
               border-radius:20px;padding:4px 12px;font-size:11px;color:#5b9dff;white-space:nowrap;">
            🔒 Login required
          </div>
        </div>
        """, unsafe_allow_html=True)

        tab_in, tab_up = st.tabs(["Sign In", "Create Account"])

        with tab_in:
            if st.session_state.cl_login_error:
                alert_error(st.session_state.cl_login_error)
                st.session_state.cl_login_error = None

            cl_mob = st.text_input("Mobile Number", placeholder="10-digit number", key="cl_mob")
            cl_pw  = st.text_input("Password", type="password", key="cl_pw")

            if st.button("Sign In & View Album", key="cl_btn_in", use_container_width=True):
                if not cl_mob or not cl_pw:
                    alert_error("Please fill all fields.")
                elif not cl_mob.isdigit() or len(cl_mob) != 10:
                    alert_error("Mobile number must be 10 digits.")
                else:
                    with st.spinner("Signing in..."):
                        resp = api_post("/login-user", json={"mobile_number": cl_mob, "password": cl_pw})
                    err = _extract_error(resp)
                    if err:
                        st.session_state.cl_login_error = err
                        st.rerun()
                    else:
                        data = resp.get("data", resp)
                        st.session_state.token       = data.get("access_token")
                        st.session_state.user_id     = data.get("user_id")
                        st.session_state.studio_name = data.get("studio_name")
                        st.session_state.username    = data.get("username")
                        nav("client_gallery")

        with tab_up:
            if st.session_state.cl_reg_error:
                alert_error(st.session_state.cl_reg_error)
                st.session_state.cl_reg_error = None

            cl_rn  = st.text_input("Full Name / Studio", key="cl_rn")
            cl_ru  = st.text_input("Username", key="cl_ru")
            cl_rm  = st.text_input("Mobile Number", placeholder="10-digit", key="cl_rm")
            cl_rpw = st.text_input("Password", type="password", key="cl_rpw")
            cl_rcp = st.text_input("Confirm Password", type="password", key="cl_rcp")

            if st.button("Create Account & View Album", key="cl_btn_reg", use_container_width=True):
                errs = []
                if not cl_rn:  errs.append("Name required.")
                if not cl_ru:  errs.append("Username required.")
                if not cl_rm or not cl_rm.isdigit() or len(cl_rm) != 10:
                    errs.append("Mobile must be 10 digits.")
                if not cl_rpw or len(cl_rpw) < 8:
                    errs.append("Password min 8 chars.")
                if cl_rpw != cl_rcp:
                    errs.append("Passwords do not match.")
                if errs:
                    st.session_state.cl_reg_error = " | ".join(errs)
                    st.rerun()
                else:
                    with st.spinner("Creating account..."):
                        resp = api_post("/register-user", json={
                            "studio_name": cl_rn, "username": cl_ru,
                            "mobile_number": cl_rm, "password": cl_rpw,
                        })
                    err = _extract_error(resp)
                    if err:
                        st.session_state.cl_reg_error = err
                        st.rerun()
                    else:
                        with st.spinner("Logging in..."):
                            lr = api_post("/login-user", json={"mobile_number": cl_rm, "password": cl_rpw})
                        data = lr.get("data", lr)
                        st.session_state.token       = data.get("access_token")
                        st.session_state.user_id     = data.get("user_id")
                        st.session_state.studio_name = data.get("studio_name")
                        st.session_state.username    = data.get("username")
                        nav("client_gallery")

        st.markdown("<div style='text-align:center;font-size:11px;color:#96a3b1;margin-top:12px'>After login, you'll be taken directly to your photos</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
_GRADIENTS = [
    "linear-gradient(135deg,#0d2045,#1a3a7a)",
    "linear-gradient(135deg,#0d3020,#1a5a3a)",
    "linear-gradient(135deg,#2d0d40,#5a1a7a)",
    "linear-gradient(135deg,#401500,#7a3a00)",
    "linear-gradient(135deg,#00102d,#002d4a)",
    "linear-gradient(135deg,#1a0030,#4a0050)",
]


def page_dashboard():
    render_navbar()
    st.markdown('<div class="fl-page">', unsafe_allow_html=True)

    with st.spinner("Loading albums..."):
        albums = api_get("/get-albums", auth=True)

    if not isinstance(albums, list):
        alert_error("Could not load albums. Please check your connection.")
        albums = []

    # Stats row
    total_photos  = sum(a.get("total_photos", 0) for a in albums)
    shared_count  = sum(1 for a in albums if a.get("is_active"))
    total_size    = sum(a.get("total_size", 0) for a in albums)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Total Albums</div><div class="stat-val">{len(albums)}</div><div class="stat-hint">{shared_count} shared publicly</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Total Photos</div><div class="stat-val">{total_photos}</div><div class="stat-hint">Across all albums</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-card"><div class="stat-label">Storage Used</div><div class="stat-val">{fmt_size(total_size)}</div><div class="stat-hint">All uploaded photos</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    hc, bc = st.columns([5, 1])
    with hc:
        st.markdown('<div class="fl-sh">📂 Your Albums</div>', unsafe_allow_html=True)
    with bc:
        if st.button("＋ New Album", key="btn_new"):
            st.session_state.create_album_open = not st.session_state.create_album_open

    # Create album form
    if st.session_state.create_album_open:
        with st.expander("➕ Create New Album", expanded=True):
            _create_album_form()

    # Albums grid
    if not albums:
        st.markdown("""<div class="fl-empty"><div class="fl-empty-icon">📭</div>
          <div class="fl-empty-title">No albums yet</div>
          <div class="fl-empty-sub">Create your first album to start uploading event photos and detecting faces automatically.</div>
        </div>""", unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for i, album in enumerate(albums):
            with cols[i % 3]:
                _album_card(album)

    st.markdown('</div>', unsafe_allow_html=True)


def _create_album_form():
    with st.form("form_create_album", clear_on_submit=True):
        aname = st.text_input("Album Name *", placeholder="e.g. Kapoor Wedding 2025")
        dc, tc = st.columns(2)
        with dc:
            edate = st.date_input("Event Date", value=date.today())
        with tc:
            st.selectbox("Event Type", ["Wedding","Corporate","Birthday","Portfolio","Other"])

        s_col, x_col = st.columns(2)
        with s_col:
            submitted = st.form_submit_button("Create Album", use_container_width=True)
        with x_col:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)

        if cancelled:
            st.session_state.create_album_open = False
            st.rerun()

        if submitted:
            if not aname:
                alert_error("Album name is required.")
            else:
                with st.spinner("Creating..."):
                    resp = api_post("/create-album",
                                    json={"album_name": aname, "event_date": str(edate)},
                                    auth=True)
                if "id" in resp:
                    alert_success(f"Album '{aname}' created!")
                    st.session_state.create_album_open = False
                    st.rerun()
                else:
                    err = _extract_error(resp)
                    alert_error(err or "Failed to create album.")


def _album_card(album):
    aid      = album.get("id","")
    name     = album.get("album_name","Untitled")
    n_photos = album.get("total_photos", 0)
    is_act   = album.get("is_active", False)
    edate    = fmt_date(album.get("event_date"))
    size     = fmt_size(album.get("total_size", 0))
    grad     = _GRADIENTS[hash(aid) % len(_GRADIENTS)]
    sdot_col = "#1d9e75" if is_act else "#ef9f27"
    slabel   = "Sharing active" if is_act else "Sharing off"
    shard_pill = '<div class="share-pill">Shared</div>' if is_act else ""
    init     = "".join(w[0].upper() for w in name.split()[:2])

    st.markdown(f"""
    <div class="album-card">
      <div class="album-thumb" style="background:{grad}">
        {shard_pill}
        <div class="album-badge">{n_photos} photos</div>
        <span style="font-size:30px;opacity:.22">{init}</span>
      </div>
      <div class="album-info">
        <div class="album-name">{name}</div>
        <div class="album-meta">{edate} · {size}</div>
        <div class="album-footer">
          <span><span class="status-dot" style="background:{sdot_col}"></span>
            <span style="font-size:11px;color:#5a6a7e">{slabel}</span></span>
          <span class="chip">{n_photos} photos</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    oc, sc = st.columns(2)
    with oc:
        if st.button("Open", key=f"open_{aid}", use_container_width=True):
            nav("album_detail", selected_album=album)
    with sc:
        if st.button("Share", key=f"share_{aid}", use_container_width=True):
            nav("share_settings", selected_album=album)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: ALBUM DETAIL
# ─────────────────────────────────────────────────────────────────────────────
def page_album_detail():
    album = st.session_state.selected_album
    if not album:
        nav("dashboard")
        return

    render_navbar(show_back=True, back_label="← Albums", back_page="dashboard")

    aid    = album.get("id","")
    name   = album.get("album_name","Album")
    edate  = fmt_date(album.get("event_date"))
    is_act = album.get("is_active", False)
    scol   = "#1d9e75" if is_act else "#ef9f27"
    slabel = "Sharing active" if is_act else "Sharing off"

    st.markdown('<div class="fl-page">', unsafe_allow_html=True)

    # Album header
    st.markdown(f"""
    <div class="fl-card-dark" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
      <div>
        <div style="font-size:20px;font-weight:600;color:#fff">{name}</div>
        <div style="display:flex;gap:14px;margin-top:6px;flex-wrap:wrap">
          <span style="font-size:12px;color:#8899bb">📅 {edate}</span>
          <span style="font-size:12px;color:#8899bb">🖼 {album.get('total_photos',0)} photos</span>
          <span style="font-size:12px;color:#8899bb">💾 {fmt_size(album.get('total_size',0))}</span>
          <span style="font-size:12px;color:{scol}">● {slabel}</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    sh_col, _ = st.columns([2, 6])
    with sh_col:
        if st.button("⚙ Share Settings", key="det_share_btn"):
            nav("share_settings", selected_album=album)

    # Upload section
    st.markdown('<div class="fl-sh" style="margin-top:1.5rem">☁ Upload Photos</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="upload-zone">
      <div style="font-size:32px;margin-bottom:8px">📤</div>
      <div style="font-size:15px;font-weight:600;color:#0d1b2a;margin-bottom:4px">Drag & drop photos here</div>
      <div style="font-size:12px;color:#5a6a7e">JPG, PNG, WEBP, BMP, TIFF supported · AI face detection runs automatically</div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Choose photos",
        type=["jpg","jpeg","png","webp","bmp","tiff","tif"],
        accept_multiple_files=True,
        key=f"uploader_{aid}",
        label_visibility="collapsed",
    )

    if uploaded:
        if st.button(f"⬆ Upload {len(uploaded)} Photo(s) & Run AI", key="do_upload_btn", use_container_width=True):
            _do_upload(aid, uploaded)

    # Upload results
    if st.session_state.upload_results:
        _render_upload_results(st.session_state.upload_results)

    # Photos gallery
    _render_album_photos(aid)

    st.markdown('</div>', unsafe_allow_html=True)


def _do_upload(album_id, files):
    total  = len(files)
    pbar   = st.progress(0, text="Preparing upload...")
    all_res = []

    for i, uf in enumerate(files):
        pbar.progress(i / total, text=f"📤 Uploading {uf.name} ({i+1}/{total}) — AI processing...")
        fb = uf.read()
        resp = api_post(
            "/upload-album-photos",
            files=[("files", (uf.name, fb, uf.type or "image/jpeg"))],
            data={"album_id": album_id},
            auth=True,
        )
        if "results" in resp:
            all_res.extend(resp.get("results", []))
        elif "error" in resp:
            all_res.append({"filename": uf.name, "status": "error", "message": resp["error"]})
        else:
            err = _extract_error(resp)
            if err:
                all_res.append({"filename": uf.name, "status": "error", "message": err})

    pbar.progress(1.0, text="✓ Upload complete!")
    st.session_state.upload_results = all_res

    # Refresh album
    updated = api_get(f"/album/{album_id}", auth=True)
    if "id" in updated:
        st.session_state.selected_album = updated

    st.rerun()


def _render_upload_results(results):
    ok_list  = [r for r in results if r.get("status") == "ok"]
    nf_list  = [r for r in results if r.get("status") == "no_face"]
    err_list = [r for r in results if r.get("status") == "error"]

    if ok_list:
        alert_success(f"{len(ok_list)} photo(s) processed with face detection.")
    if nf_list:
        alert_info(f"{len(nf_list)} photo(s) uploaded — no face detected in them.")
    if err_list:
        msgs = "; ".join(r.get("message","error") for r in err_list[:2])
        alert_error(f"{len(err_list)} photo(s) failed: {msgs}")

    if st.button("Clear", key="clr_res"):
        st.session_state.upload_results = None
        st.rerun()


def _render_album_photos(album_id):
    with st.spinner("Loading photos..."):
        gal = api_get("/gallery", auth=True)

    if "error" in gal:
        alert_error("Could not load photos.")
        return

    target = next(
        (a for a in gal.get("albums", []) if str(a.get("album_id")) == str(album_id)),
        None,
    )

    if not target:
        st.markdown("""<div class="fl-empty"><div class="fl-empty-icon">📭</div>
          <div class="fl-empty-title">No photos yet</div>
          <div class="fl-empty-sub">Upload photos above and AI will automatically detect faces.</div>
        </div>""", unsafe_allow_html=True)
        return

    all_photos = []
    for pg in target.get("persons", []):
        all_photos.extend(pg.get("photos", []))

    n = len(all_photos)
    st.markdown(f'<div class="fl-sh">🖼 Photos<span class="fl-cb">{n} total</span></div>', unsafe_allow_html=True)

    if not all_photos:
        st.markdown('<div class="fl-empty"><div class="fl-empty-icon">📭</div><div class="fl-empty-title">No photos uploaded yet</div></div>', unsafe_allow_html=True)
        return

    per_row = 5
    cols = st.columns(per_row)
    for i, photo in enumerate(all_photos):
        with cols[i % per_row]:
            iurl = image_url(photo.get("img_path",""))
            pid  = photo.get("person_id","") or ""
            tag  = pid[:8] if pid else "No face"
            st.markdown(f"""
            <div class="photo-item">
              <img src="{iurl}" style="width:100%;height:110px;object-fit:cover;border-radius:8px;display:block"
                   onerror="this.style.background='#1a3060';this.style.minHeight='110px';this.removeAttribute('src')"/>
              <div class="photo-person-tag">{tag}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: SHARE SETTINGS
# ─────────────────────────────────────────────────────────────────────────────
def page_share_settings():
    album = st.session_state.selected_album
    if not album:
        nav("dashboard")
        return

    render_navbar(show_back=True, back_label="← Album", back_page="album_detail")

    aid      = album.get("id","")
    name     = album.get("album_name","Album")
    is_act   = st.session_state.selected_album.get("is_active", False)
    s_link   = st.session_state.selected_album.get("share_link","")

    st.markdown('<div class="fl-page">', unsafe_allow_html=True)

    _, mc, _ = st.columns([1, 3, 1])
    with mc:
        st.markdown(f"""
        <div class="fl-card">
          <div style="font-size:18px;font-weight:600;color:#0d1b2a;margin-bottom:4px">Share Album</div>
          <div style="font-size:13px;color:#5a6a7e">{name}</div>
        </div>
        """, unsafe_allow_html=True)

        # Sharing status
        act_label = "Active" if is_act else "Disabled"
        act_color = "#1d9e75" if is_act else "#ef9f27"
        st.markdown(f"""
        <div style="background:#f8fafc;border:.5px solid #e2e8f0;border-radius:10px;padding:14px 16px;
             display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <div>
            <div style="font-size:14px;font-weight:500;color:#0d1b2a">Public Sharing</div>
            <div style="font-size:11px;color:#5a6a7e;margin-top:2px">
              Currently: <b style="color:{act_color}">{act_label}</b>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        tc, gc = st.columns(2)
        with tc:
            if st.button("Toggle Sharing On/Off", key="btn_toggle", use_container_width=True):
                with st.spinner("Updating..."):
                    resp = api_post("/album/toggle-share", json={"album_id": aid}, auth=True)
                if "album_id" in resp:
                    st.session_state.selected_album = {
                            **st.session_state.selected_album,
                        "is_active": resp.get("is_active"),
                        "share_link": resp.get("share_link"),
                    }
                    st.rerun()
                else:
                    alert_error(_extract_error(resp) or "Toggle failed.")

        with gc:
            if st.button("Generate New Link", key="btn_gen", use_container_width=True):
                with st.spinner("Generating..."):
                    resp = api_post("/album/generate-share-link", json={"album_id": aid}, auth=True)
                if "share_link" in resp:
                    st.session_state.selected_album = {
                        **st.session_state.selected_album,
                        "is_active": resp.get("is_active", True),
                        "share_link": resp.get("share_link"),
                    }
                    alert_success("Share link generated!")
                    st.rerun()
                else:
                    alert_error(_extract_error(resp) or "Failed to generate link.")

        # Show link
        cur_link = st.session_state.selected_album.get("share_link") or s_link
        if cur_link:
            full_url = f"http://localhost:8501/?share={cur_link}"
            st.markdown(f"""
            <div style="margin-top:16px">
              <div style="font-size:11px;font-weight:500;color:#5a6a7e;text-transform:uppercase;
                   letter-spacing:.5px;margin-bottom:8px">Share Link</div>
              <div class="share-link-box">🔗 {full_url}</div>
            </div>
            """, unsafe_allow_html=True)
            st.code(full_url, language=None)
            alert_info("Share this link with your clients. They'll need to sign in or create an account to view photos.")
        else:
            alert_info("No share link yet — click 'Generate New Link' to create one.")

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: CLIENT GALLERY
# ─────────────────────────────────────────────────────────────────────────────
def page_client_gallery():
    share_token = st.session_state.share_link_pending
    studio      = st.session_state.studio_name or "Client"
    initials    = "".join(w[0].upper() for w in studio.split()[:2])

    st.markdown(f"""
    <div class="fl-nav">
      <div class="fl-logo">
        <div class="fl-logo-icon">🔗</div>
        <span class="fl-logo-text">FaceLinkAI</span>
      </div>
      <div class="fl-nav-right">
        <span class="fl-studio-name">{studio}</span>
        <div class="fl-avatar">{initials}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if not share_token:
        st.markdown('<div class="fl-page"><div class="fl-empty"><div class="fl-empty-icon">🔒</div><div class="fl-empty-title">No share token found</div></div></div>', unsafe_allow_html=True)
        return

    with st.spinner("Loading shared album..."):
        resp = api_get(f"/album/share/{share_token}", auth=True)

    if isinstance(resp, dict):
        detail = resp.get("detail","")
        if detail == "LOGIN_REQUIRED" or (isinstance(detail,dict) and not detail.get("status",True)):
            nav("client_login")
            return
        if "error" in resp:
            alert_error(f"Could not load album: {resp['error']}")
            return

    album_id   = resp.get("album_id","")
    album_name = resp.get("album_name","Shared Album")
    edate      = fmt_date(resp.get("event_date"))
    photos     = resp.get("photos",[])
    total      = resp.get("total_photos", len(photos))

    st.markdown('<div class="fl-page">', unsafe_allow_html=True)

    # Banner
    st.markdown(f"""
    <div class="fl-card-dark" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <div style="font-size:20px;font-weight:600;color:#fff">{album_name}</div>
        <div style="font-size:12px;color:#8899bb;margin-top:4px">📅 {edate}</div>
        <div style="display:flex;gap:8px;margin-top:8px">
          <span style="background:rgba(26,109,255,.2);border:.5px solid rgba(26,109,255,.35);
               border-radius:20px;padding:3px 10px;font-size:11px;color:#5b9dff">📸 {total} photos</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Action bar
    fc, dc, lc = st.columns([2, 2, 1])
    with fc:
        if st.button("🔍 Find My Photos", key="cl_find", use_container_width=True):
            st.session_state.recog_step    = 1
            st.session_state.recog_results = None
            st.session_state.selfie_file   = None
            nav("face_recognition")
    with dc:
        if photos and st.button("⬇ Download All", key="cl_dl_all", use_container_width=True):
            _bulk_download(photos)
    with lc:
        if st.button("Logout", key="cl_logout"):
            logout()

    # Photo grid
    st.markdown(f'<div class="fl-sh">🖼 All Photos<span class="fl-cb">{total}</span></div>', unsafe_allow_html=True)

    if not photos:
        st.markdown("""<div class="fl-empty"><div class="fl-empty-icon">📭</div>
          <div class="fl-empty-title">No photos in this album yet</div>
        </div>""", unsafe_allow_html=True)
    else:
        per_row = 4
        cols = st.columns(per_row)
        for i, photo in enumerate(photos):
            with cols[i % per_row]:
                iurl = image_url(photo.get("img_path",""))
                pid  = photo.get("person_id","") or ""
                tag  = pid[:8] if pid else "No face"
                st.markdown(f"""
                <div class="photo-item">
                  <img src="{iurl}" style="width:100%;height:130px;object-fit:cover;border-radius:8px;display:block"
                       onerror="this.style.background='#1a3060';this.style.minHeight='130px';this.removeAttribute('src')"/>
                  <div class="photo-person-tag">{tag}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def _bulk_download(photos):
    with st.spinner("Preparing ZIP..."):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, p in enumerate(photos):
                url = image_url(p.get("img_path",""))
                try:
                    r = requests.get(url, timeout=15)
                    if r.status_code == 200:
                        ext = p.get("img_path","photo.jpg").rsplit(".",1)[-1]
                        zf.writestr(f"photo_{i+1:04d}.{ext}", r.content)
                except Exception:
                    pass
        buf.seek(0)
    st.download_button(
        label="💾 Click to Download ZIP",
        data=buf,
        file_name="album_photos.zip",
        mime="application/zip",
        key="zip_dl_btn",
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE: FACE RECOGNITION
# ─────────────────────────────────────────────────────────────────────────────
def page_face_recognition():
    studio   = st.session_state.studio_name or "Client"
    initials = "".join(w[0].upper() for w in studio.split()[:2])
    st.markdown(f"""
    <div class="fl-nav">
      <div class="fl-logo">
        <div class="fl-logo-icon">🔗</div>
        <span class="fl-logo-text">FaceLinkAI</span>
      </div>
      <div class="fl-nav-right">
        <span class="fl-studio-name">{studio}</span>
        <div class="fl-avatar">{initials}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="fl-page">', unsafe_allow_html=True)

    # Step indicator
    step = st.session_state.recog_step
    steps_data = [("1","Upload selfie"),("2","AI scanning"),("3","View results")]
    html_steps = ""
    for idx,(num,label) in enumerate(steps_data):
        s   = int(num)
        cls = "active" if s == step else ("done" if s < step else "idle")
        html_steps += f'<div class="fl-step {cls}"><div class="fl-step-num {cls}">{num}</div><span class="fl-step-label">{label}</span></div>'
        if idx < len(steps_data) - 1:
            html_steps += '<div class="fl-step-conn"></div>'
    st.markdown(f'<div class="fl-steps">{html_steps}</div>', unsafe_allow_html=True)

    bc, _ = st.columns([2, 8])
    with bc:
        if st.button("← Back to Album", key="recog_back_nav"):
            nav("client_gallery")

    if step == 1:
        _recog_upload()
    elif step == 2:
        _recog_scan()
    elif step == 3:
        _recog_results()

    st.markdown('</div>', unsafe_allow_html=True)


def _recog_upload():
    _, cc, _ = st.columns([1, 3, 1])
    with cc:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem">
          <div style="font-size:22px;font-weight:600;color:#0d1b2a;margin-bottom:6px">Find Your Photos</div>
          <div style="font-size:14px;color:#5a6a7e;line-height:1.6">Upload a clear selfie — AI will find all photos of you in this album</div>
        </div>
        <div class="upload-zone">
          <div style="font-size:42px;margin-bottom:8px">🤳</div>
          <div style="font-size:15px;font-weight:600;color:#0d1b2a;margin-bottom:4px">Upload your selfie</div>
          <div style="font-size:12px;color:#5a6a7e">Clear, well-lit, solo photo · JPG or PNG</div>
        </div>
        """, unsafe_allow_html=True)

        selfie = st.file_uploader("Choose selfie", type=["jpg","jpeg","png","webp"],
                                   key="selfie_up", label_visibility="collapsed")

        if selfie:
            st.image(selfie, width=160, caption="Your selfie — ready to scan")

        # Tips
        t1, t2, t3 = st.columns(3)
        for col, icon, title, hint in [
            (t1,"☀️","Good lighting","Avoid shadows"),
            (t2,"🎯","Face centered","Look at camera"),
            (t3,"🖼","Solo photo","Only your face"),
        ]:
            with col:
                st.markdown(f'<div class="fl-card" style="text-align:center;padding:10px"><div style="font-size:18px">{icon}</div><div style="font-size:12px;font-weight:500;color:#0d1b2a;margin-top:4px">{title}</div><div style="font-size:10px;color:#96a3b1">{hint}</div></div>', unsafe_allow_html=True)

        if selfie:
            if st.button("🔍 Scan & Find My Photos", key="btn_scan", use_container_width=True):
                st.session_state.selfie_file = selfie
                st.session_state.recog_step  = 2
                st.rerun()


def _recog_scan():
    _, cc, _ = st.columns([1, 3, 1])
    with cc:
        st.markdown("""
        <div style="text-align:center;margin-bottom:1.5rem">
          <div style="font-size:22px;font-weight:600;color:#0d1b2a">Scanning for matches...</div>
          <div style="font-size:14px;color:#5a6a7e;margin-top:6px">AI is analysing your selfie against all album photos</div>
        </div>
        """, unsafe_allow_html=True)

    selfie = st.session_state.get("selfie_file")
    if not selfie:
        st.session_state.recog_step = 1
        st.rerun()
        return

    with st.spinner("🤖 Running face recognition AI... this may take a moment."):
        try:
            fb = selfie.read() if hasattr(selfie, "read") else selfie.getvalue()
        except Exception:
            alert_error("Could not read selfie file.")
            st.session_state.recog_step = 1
            st.rerun()
            return

        resp = api_post("/recognize-face",
                        files=[("file", (selfie.name, fb, selfie.type or "image/jpeg"))],
                        auth=True)

    err = _extract_error(resp)
    if err:
        alert_error(err)
        if st.button("Try Again", key="scan_retry"):
            st.session_state.recog_step = 1
            st.rerun()
        return

    st.session_state.recog_results = resp
    st.session_state.recog_step    = 3
    st.rerun()


def _recog_results():
    res = st.session_state.recog_results
    if not res:
        st.session_state.recog_step = 1
        st.rerun()
        return

    matched    = res.get("matched_photos", [])
    person_id  = res.get("person_id")
    sim        = res.get("similarity_score")
    is_new     = res.get("is_new_person", True)
    n_matches  = len(matched)

    _, cc, _ = st.columns([1, 4, 1])
    with cc:
        sim_txt = f"{sim:.0%} confidence" if sim else "Scanned all photos"
        st.markdown(f"""
        <div class="fl-card-dark" style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
          <div style="width:52px;height:52px;border-radius:50%;background:#1a3a7a;border:2px solid #1a6dff;
               display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0">🤳</div>
          <div style="flex:1;min-width:0">
            <div style="font-size:16px;font-weight:600;color:#fff">Your face match results</div>
            <div style="font-size:12px;color:#8899bb;margin-top:3px">{sim_txt}</div>
          </div>
          <div style="background:rgba(29,158,117,.2);border:.5px solid rgba(29,158,117,.4);
               border-radius:12px;padding:8px 16px;text-align:center;flex-shrink:0">
            <div style="font-size:22px;font-weight:600;color:#5dcaa5">{n_matches}</div>
            <div style="font-size:10px;color:#5dcaa5">photos found</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # No matches
    if is_new or n_matches == 0:
        st.markdown("""<div class="fl-empty">
          <div class="fl-empty-icon">😔</div>
          <div class="fl-empty-title">No matching photos found</div>
          <div class="fl-empty-sub">Try a different photo with better lighting and a clear, direct view of your face.</div>
        </div>""", unsafe_allow_html=True)
        ra, rb = st.columns(2)
        with ra:
            if st.button("Try Another Photo", key="retry_photo", use_container_width=True):
                st.session_state.recog_step    = 1
                st.session_state.recog_results = None
                st.session_state.selfie_file   = None
                st.rerun()
        with rb:
            if st.button("← Back to Album", key="back_from_no_match", use_container_width=True):
                nav("client_gallery")
        return

    # Scanning steps done banner
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;flex-wrap:wrap">
      {"".join([f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#1d9e75"><span style="width:16px;height:16px;border-radius:50%;background:#1d9e75;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:9px">✓</span>{s}</span><span style="width:14px;height:1px;background:#cbd5e1;display:inline-block"></span>' for s in ["Face detected","Embedding generated",f"{n_matches} matches found"]][:-1])}
      <span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#1d9e75"><span style="width:16px;height:16px;border-radius:50%;background:#1d9e75;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-size:9px">✓</span>{n_matches} matches found</span>
    </div>
    """, unsafe_allow_html=True)

    # Matched photos grid
    per_row = 4
    cols    = st.columns(per_row)
    for i, photo in enumerate(matched):
        with cols[i % per_row]:
            iurl  = image_url(photo.get("img_path",""))
            sim_p = f"{photo.get('similarity',0)*100:.0f}%"
            aname = photo.get("album_name","")
            st.markdown(f"""
            <div class="match-card">
              <img src="{iurl}" style="width:100%;height:130px;object-fit:cover;display:block"
                   onerror="this.style.background='#1a3060';this.style.minHeight='130px';this.removeAttribute('src')"/>
              <div class="match-ob">Match</div>
              <div class="match-cb">{sim_p}</div>
            </div>
            <div style="font-size:10px;color:#5a6a7e;margin-bottom:8px">{aname}</div>
            """, unsafe_allow_html=True)

    # Download + back
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="fl-card" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px">
      <div>
        <div style="font-size:14px;font-weight:500;color:#0d1b2a">{n_matches} photos matched to your face</div>
        <div style="font-size:11px;color:#5a6a7e;margin-top:2px">Original resolution</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    da, db, dc = st.columns(3)
    with da:
        if st.button(f"⬇ Download {n_matches} Photos", key="dl_matched_btn", use_container_width=True):
            _bulk_download(matched)
    with db:
        if st.button("← Back to Album", key="back_after_match", use_container_width=True):
            nav("client_gallery")
    with dc:
        if st.button("Try Another Selfie", key="retry_selfie_final", use_container_width=True):
            st.session_state.recog_step    = 1
            st.session_state.recog_results = None
            st.session_state.selfie_file   = None
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────────────────────────────────────
def main():
    page = st.session_state.page

    # Auth guard — protected studio pages
    if page in ["dashboard", "album_detail", "share_settings"] and not st.session_state.token:
        st.session_state.page = "login"
        page = "login"

    # Client pages need token too
    if page in ["client_gallery", "face_recognition"] and not st.session_state.token:
        st.session_state.page = "client_login"
        page = "client_login"

    routes = {
        "login":           page_login,
        "client_login":    page_client_login,
        "dashboard":       page_dashboard,
        "album_detail":    page_album_detail,
        "share_settings":  page_share_settings,
        "client_gallery":  page_client_gallery,
        "face_recognition":page_face_recognition,
    }

    routes.get(page, page_login)()


if __name__ == "__main__":
    main()