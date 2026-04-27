# ═══════════════════════════════════════════════════════════════════════════════
# FaceLinkAI – Studio Edition  |  Streamlit Frontend
# Connects to FastAPI backend at http://localhost:8000
# Run:  streamlit run app.py
# ═══════════════════════════════════════════════════════════════════════════════

import io
import time
from datetime import datetime
from typing import Optional

import requests
import streamlit as st
from PIL import Image

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_URL   = "http://localhost:8000"
IMAGE_BASE = f"{BASE_URL}/images"

st.set_page_config(
    page_title="FaceLinkAI – Studio Edition",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS  – matches the purple/teal/amber design palette from the mockups
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

:root {
    --brand:        #7F77DD;
    --brand-light:  #EEEDFE;
    --brand-mid:    #CECBF6;
    --brand-dark:   #534AB7;
    --teal:         #1D9E75;
    --teal-light:   #E1F5EE;
    --amber:        #BA7517;
    --amber-light:  #FAEEDA;
    --coral:        #D85A30;
    --coral-light:  #FDEEE8;
    --surface:      #FFFFFF;
    --bg:           #F7F7FB;
    --border:       #E4E3F5;
    --text:         #1A1A2E;
    --muted:        #6B6B8A;
    --radius:       12px;
    --shadow:       0 1px 3px rgba(127,119,221,.10), 0 4px 16px rgba(127,119,221,.07);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Page background ── */
.stApp { background: var(--bg); }
.main .block-container {
    padding: 1.8rem 2.2rem 2rem;
    max-width: 1320px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1rem .9rem;
}

/* ── Primary buttons ── */
.stButton > button {
    background: var(--brand) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: .85rem !important;
    padding: .42rem 1.1rem !important;
    transition: opacity .15s ease, box-shadow .15s ease !important;
    box-shadow: 0 1px 4px rgba(127,119,221,.25) !important;
}
.stButton > button:hover {
    opacity: .88 !important;
    box-shadow: 0 3px 10px rgba(127,119,221,.35) !important;
}
.stButton > button:active { opacity: .75 !important; }

/* ── Inputs ── */
.stTextInput input,
.stPasswordInput input,
.stDateInput input,
.stTextArea textarea {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .88rem !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    transition: border-color .15s !important;
}
.stTextInput input:focus,
.stPasswordInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(127,119,221,.14) !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: .85rem 1rem .8rem;
    box-shadow: var(--shadow);
}
[data-testid="stMetricLabel"] {
    font-size: .72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: .06em !important;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border);
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: .85rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    padding: .55rem 1.2rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--brand) !important;
    border-bottom: 2px solid var(--brand) !important;
    background: transparent !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: .88rem !important;
    color: var(--text) !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
.streamlit-expanderContent {
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 var(--radius) var(--radius) !important;
    background: var(--surface) !important;
    padding: .8rem 1rem !important;
}

/* ── Alert / info boxes ── */
.stAlert {
    border-radius: var(--radius) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .85rem !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 1.5px dashed var(--border) !important;
    border-radius: var(--radius) !important;
    background: var(--bg) !important;
    padding: .5rem !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }

/* ── Custom card ── */
.fl-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.15rem;
    box-shadow: var(--shadow);
    margin-bottom: .75rem;
}

/* ── Badges ── */
.fl-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: .7rem;
    font-weight: 600;
    letter-spacing: .04em;
    font-family: 'DM Sans', sans-serif;
}
.badge-ok       { background: var(--teal-light);  color: var(--teal); }
.badge-noface   { background: var(--amber-light); color: var(--amber); }
.badge-error    { background: var(--coral-light); color: var(--coral); }
.badge-active   { background: var(--teal-light);  color: var(--teal); }
.badge-inactive { background: #EDEDF5;            color: var(--muted); }

/* ── Person chips ── */
.person-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--brand-light);
    color: var(--brand-dark);
    border-radius: 20px;
    padding: 3px 10px;
    font-size: .75rem;
    font-weight: 500;
    font-family: 'DM Mono', monospace;
    margin: 2px;
}

/* ── Brand logo ── */
.brand-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: .5rem .1rem 1.1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: .9rem;
}
.brand-dot {
    width: 34px; height: 34px;
    border-radius: 50%;
    background: var(--brand-light);
    border: 1.5px solid var(--brand);
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.brand-dot-core {
    width: 13px; height: 13px;
    border-radius: 50%;
    background: var(--brand);
}
.brand-name { font-size: .97rem; font-weight: 600; color: var(--text); line-height:1.1; }
.brand-sub  { font-size: .67rem; color: var(--brand); font-weight: 500; letter-spacing:.03em; }

/* ── Section label ── */
.section-label {
    font-size: .67rem;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1rem 0 .35rem;
}

/* ── Sidebar nav button active style ── */
.nav-active > button {
    background: var(--brand-light) !important;
    color: var(--brand-dark) !important;
    box-shadow: none !important;
}

/* ── Progress bar ── */
.stProgress > div > div { background: var(--brand) !important; border-radius: 4px !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: var(--brand) !important; }

/* ── Caption ── */
.stImage caption, .stCaption { font-size: .72rem !important; color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def _init_state():
    defaults = {
        "token":        None,
        "studio_name":  None,
        "user_id":      None,
        "page":         "login",
        "active_album": None,
        "share_token":  None,
        "_face_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


def _goto(page: str, **kwargs):
    st.session_state.page = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


def _is_logged_in() -> bool:
    return bool(st.session_state.token)


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _api(method: str, path: str, *, auth: bool = True, **kwargs):
    """Returns (data | None, error_str | None)."""
    headers = kwargs.pop("headers", {})
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.request(
            method, f"{BASE_URL}{path}",
            headers=headers, timeout=90, **kwargs
        )
        if r.status_code in (200, 201):
            try:
                return r.json(), None
            except Exception:
                return r.text, None
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return None, str(detail)
    except requests.exceptions.ConnectionError:
        return None, "❌ Cannot reach http://localhost:8000. Is FastAPI running?"
    except Exception as exc:
        return None, str(exc)


def api_register(studio_name, mobile, email, password):
    payload = {
        "studio_name":   studio_name,
        "mobile_number": mobile,
        "email":         email or None,
        "password":      password,
    }
    return _api("POST", "/register-user", auth=False, json=payload)


def api_login(mobile, password):
    return _api("POST", "/login-user", auth=False,
                json={"mobile_number": mobile, "password": password})


def api_create_album(name, event_name, event_date):
    payload = {"album_name": name}
    if event_name: payload["event_name"] = event_name
    if event_date: payload["event_date"] = str(event_date)
    return _api("POST", "/create-album", json=payload)


def api_get_albums():
    return _api("GET", "/get-albums")


def api_upload_photos(album_id: str, files: list):
    """files: list of (filename, bytes, mime_type)"""
    multipart = [("files", (fn, data, mime)) for fn, data, mime in files]
    return _api("POST", "/upload-album-photos",
                data={"album_id": album_id}, files=multipart)


def api_recognize(img_bytes: bytes, filename: str):
    return _api("POST", "/recognize-face",
                files={"file": (filename, img_bytes, "image/jpeg")})


def api_gallery():
    return _api("GET", "/gallery")


def api_share_album(share_link: str):
    return _api("GET", f"/album/share/{share_link}", auth=False)


def api_generate_share_link(album_id: str):
    return _api("POST", f"/album/{album_id}/generate-share-link")


def api_toggle_share(album_id: str):
    return _api("POST", f"/album/{album_id}/toggle-share")


# ═══════════════════════════════════════════════════════════════════════════════
# UI UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def _image_url(img_path: str) -> str:
    return f"{IMAGE_BASE}/{img_path}"


def _show_logo():
    st.markdown("""
    <div class="brand-logo">
        <div class="brand-dot"><div class="brand-dot-core"></div></div>
        <div>
            <div class="brand-name">FaceLinkAI</div>
            <div class="brand-sub">Studio Edition</div>
        </div>
    </div>""", unsafe_allow_html=True)


def _badge(status: str) -> str:
    mapping = {
        "ok":       ("badge-ok",       "✓ Face found"),
        "no_face":  ("badge-noface",   "⚠ No face"),
        "error":    ("badge-error",    "✕ Error"),
        "active":   ("badge-active",   "● Sharing on"),
        "inactive": ("badge-inactive", "○ Sharing off"),
    }
    cls, label = mapping.get(status, ("badge-error", status))
    return f'<span class="fl-badge {cls}">{label}</span>'


def _fmt_size(n: int) -> str:
    if n < 1024:       return f"{n} B"
    if n < 1024**2:    return f"{n/1024:.1f} KB"
    if n < 1024**3:    return f"{n/1024**2:.1f} MB"
    return f"{n/1024**3:.2f} GB"


def _show_image_safe(url: str, caption: str = ""):
    """Render an image from URL; show a grey tile on failure."""
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            img = Image.open(io.BytesIO(r.content))
            st.image(img, caption=caption or None, width="stretch")
            return
    except Exception:
        pass
    st.markdown(
        '<div style="background:#EDEDF5;border-radius:8px;aspect-ratio:1;'
        'display:flex;align-items:center;justify-content:center;'
        'color:#9999B5;font-size:.7rem;">no image</div>',
        unsafe_allow_html=True,
    )


def _album_color(idx: int) -> str:
    palette = ["#CECBF6", "#9FE1CB", "#F5C4B3", "#B5D4F4", "#FAD4A0",
               "#D4EFB0", "#F9C9E0", "#C5E8F5", "#E8C9FA", "#F5E4C0"]
    return palette[idx % len(palette)]


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

def _render_sidebar():
    with st.sidebar:
        _show_logo()

        if _is_logged_in():
            initials = (st.session_state.studio_name or "S")[:2].upper()
            st.markdown(f"""
            <div class="fl-card" style="margin-bottom:1rem;padding:.75rem 1rem;">
                <div style="display:flex;align-items:center;gap:10px;">
                    <div style="width:36px;height:36px;border-radius:50%;
                         background:var(--brand-mid);display:flex;align-items:center;
                         justify-content:center;font-weight:600;font-size:.85rem;
                         color:var(--brand-dark);flex-shrink:0;">{initials}</div>
                    <div>
                        <div style="font-weight:600;font-size:.85rem;color:var(--text);
                             line-height:1.2;">
                            {st.session_state.studio_name or "Studio"}</div>
                        <div style="font-size:.7rem;color:var(--muted);">Studio account</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            st.markdown('<div class="section-label">Navigation</div>', unsafe_allow_html=True)

            current = st.session_state.page
            nav = [
                ("🏠", "Dashboard",   "dashboard"),
                ("🖼️", "Gallery",     "gallery"),
                ("🔍", "Face Search", "face_search"),
            ]
            for icon, label, target in nav:
                is_active = current == target
                container = st.container()
                if is_active:
                    container.markdown(
                        f'<div style="background:var(--brand-light);border-radius:8px;'
                        f'padding:.35rem .6rem .35rem .7rem;margin-bottom:3px;cursor:default;">'
                        f'<span style="color:var(--brand-dark);font-weight:600;font-size:.85rem;">'
                        f'{icon}&nbsp;&nbsp;{label}</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(f"{icon}  {label}", key=f"nav_{label}",
                                 width="stretch"):
                        _goto(target)

            st.markdown('<div class="section-label" style="margin-top:1.2rem;">Quick share</div>',
                        unsafe_allow_html=True)
            share_input = st.text_input("Share token", placeholder="paste token…",
                                        label_visibility="collapsed", key="sidebar_share")
            if st.button("Open shared album", width="stretch", key="sidebar_open_share"):
                token = share_input.strip()
                if token:
                    _goto("share_view", share_token=token)
                else:
                    st.warning("Paste a share token first.")

            st.markdown("---")
            if st.button("⬆  Logout", width="stretch", key="sidebar_logout"):
                for k in ("token", "studio_name", "user_id",
                          "active_album", "_face_result"):
                    st.session_state[k] = None
                _goto("login")

        else:
            st.markdown('<div class="section-label">Account</div>', unsafe_allow_html=True)
            if st.button("Login",    width="stretch"): _goto("login")
            if st.button("Register", width="stretch"): _goto("register")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: LOGIN
# ═══════════════════════════════════════════════════════════════════════════════

def page_login():
    _, col, _ = st.columns([1, 1, 1])
    with col:
        # Logo block
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 0 1.8rem;">
            <div style="width:60px;height:60px;border-radius:50%;
                 background:var(--brand-light);border:2px solid var(--brand);
                 display:flex;align-items:center;justify-content:center;
                 margin:0 auto 14px;">
                <div style="width:22px;height:22px;border-radius:50%;
                     background:var(--brand);"></div>
            </div>
            <div style="font-size:1.55rem;font-weight:600;color:var(--text);">
                FaceLinkAI</div>
            <div style="font-size:.78rem;color:var(--brand);font-weight:500;
                 margin-top:3px;letter-spacing:.04em;">Studio Edition</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("#### Welcome back")
        st.caption("Sign in to your studio account")

        mobile   = st.text_input("Mobile number", placeholder="9876543210",
                                 key="login_mobile")
        password = st.text_input("Password", type="password",
                                 placeholder="••••••••", key="login_pw")

        col_btn, col_link = st.columns([2, 1])
        with col_btn:
            login_clicked = st.button("Sign in →", width="stretch",
                                      key="do_login")
        if login_clicked:
            if not mobile or not password:
                st.error("Fill in both fields.")
            else:
                with st.spinner("Signing in…"):
                    data, err = api_login(mobile, password)
                if err:
                    st.error(f"Login failed: {err}")
                else:
                    st.session_state.token       = data["access_token"]
                    st.session_state.studio_name = data["studio_name"]
                    st.session_state.user_id     = data.get("user_id")
                    _goto("dashboard")

        st.markdown("---")
        st.caption("New studio?")
        if st.button("Create studio account", width="stretch",
                     key="goto_register"):
            _goto("register")
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: REGISTER
# ═══════════════════════════════════════════════════════════════════════════════

def page_register():
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 0 1.8rem;">
            <div style="font-size:1.55rem;font-weight:600;color:var(--text);">
                Create studio</div>
            <div style="font-size:.8rem;color:var(--muted);margin-top:4px;">
                Join FaceLinkAI — Studio Edition</div>
        </div>""", unsafe_allow_html=True)

       

        studio_name = st.text_input("Studio name *",      key="reg_studio")
        mobile      = st.text_input("Mobile number *",    key="reg_mobile",
                                    placeholder="9876543210")
        email       = st.text_input("Email (optional)",   key="reg_email",
                                    placeholder="studio@example.com")
        pw1         = st.text_input("Password *",         key="reg_pw1",
                                    type="password")
        pw2         = st.text_input("Confirm password *", key="reg_pw2",
                                    type="password")

        if st.button("Create account", width="stretch", key="do_register"):
            if not all([studio_name, mobile, pw1, pw2]):
                st.error("Please fill all required (*) fields.")
            elif pw1 != pw2:
                st.error("Passwords do not match.")
            elif len(pw1) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                with st.spinner("Creating account…"):
                    data, err = api_register(studio_name, mobile, email, pw1)
                if err:
                    st.error(f"Registration failed: {err}")
                else:
                    st.success("✓ Account created! Redirecting to login…")
                    time.sleep(1.4)
                    _goto("login")

        st.markdown("---")
        if st.button("← Back to login", width="stretch", key="back_login"):
            _goto("login")
        st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def page_dashboard():
    # ── Page header ──────────────────────────────────────────────────────────
    hc1, hc2 = st.columns([3, 1])
    with hc1:
        st.markdown("## Studio Dashboard")
        st.markdown(
            f'<p style="color:var(--muted);margin-top:-.6rem;font-size:.83rem;">'
            f'{datetime.now().strftime("%A, %d %B %Y")}'
            f'  ·  {st.session_state.studio_name or ""}</p>',
            unsafe_allow_html=True,
        )
    with hc2:
        if st.button("＋ Create event", width="stretch", key="toggle_create"):
            st.session_state["_show_create"] = not st.session_state.get("_show_create", False)
            st.rerun()

    # ── Create album panel ────────────────────────────────────────────────────
    if st.session_state.get("_show_create"):
        st.markdown("""
        <div class="fl-card" style="border-left:3px solid var(--brand);margin-bottom:1rem;">
        """, unsafe_allow_html=True)
        st.markdown("#### New event album")
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            new_name = st.text_input("Album name *", key="na_name")
        with fc2:
            new_ename = st.text_input("Event name", key="na_ename",
                                      placeholder="e.g. Sharma Wedding")
        with fc3:
            new_date  = st.date_input("Event date", key="na_date", value=None)
        bc1, bc2, _ = st.columns([1, 1, 4])
        with bc1:
            if st.button("Create album", key="do_create_album"):
                if not new_name:
                    st.error("Album name is required.")
                else:
                    with st.spinner("Creating…"):
                        d, e = api_create_album(
                            st.session_state.na_name,
                            st.session_state.get("na_ename", ""),
                            st.session_state.get("na_date"),
                        )
                    if e:
                        st.error(e)
                    else:
                        st.success(f"✓ Album '{d['album_name']}' created!")
                        st.session_state["_show_create"] = False
                        time.sleep(.7)
                        st.rerun()
        with bc2:
            if st.button("Cancel", key="cancel_create"):
                st.session_state["_show_create"] = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Load albums ───────────────────────────────────────────────────────────
    with st.spinner("Loading events…"):
        albums, err = api_get_albums()

    if err:
        st.error(err)
        return

    if not albums:
        st.markdown("""
        <div class="fl-card" style="text-align:center;padding:3.5rem 1rem;">
            <div style="font-size:2.8rem;margin-bottom:.6rem;">📁</div>
            <div style="font-weight:600;font-size:1rem;color:var(--text);">No events yet</div>
            <div style="color:var(--muted);font-size:.83rem;margin-top:.3rem;">
                Click "Create event" above to upload your first album.</div>
        </div>""", unsafe_allow_html=True)
        return

    # ── Stats row ─────────────────────────────────────────────────────────────
    total_photos = sum(a.get("total_photos", 0) for a in albums)
    total_size   = sum(a.get("total_size",   0) for a in albums)
    active_links = sum(1 for a in albums if a.get("is_active"))

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Total events",  len(albums))
    sc2.metric("Total photos",  f"{total_photos:,}")
    sc3.metric("Storage used",  _fmt_size(total_size))
    sc4.metric("Active links",  active_links)

    st.markdown("---")
    st.markdown("### Recent events")

    # ── Album grid ────────────────────────────────────────────────────────────
    grid_cols = st.columns(3)
    for idx, album in enumerate(albums):
        a_id       = album.get("id", "")
        is_active  = album.get("is_active", False)
        share_tok  = album.get("share_link", "")
        bg         = _album_color(idx)
        initial    = (album.get("album_name") or "?")[:1].upper()

        with grid_cols[idx % 3]:
            # Card header (colour band)
            st.markdown(f"""
            <div style="background:{bg};border-radius:12px 12px 0 0;height:78px;
                 display:flex;align-items:center;justify-content:space-between;
                 padding:0 1rem;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="width:34px;height:34px;border-radius:50%;
                         background:rgba(0,0,0,.12);border:2px solid rgba(255,255,255,.7);
                         display:flex;align-items:center;justify-content:center;
                         font-weight:600;font-size:.85rem;color:rgba(255,255,255,.9);">
                        {initial}
                    </div>
                    <span style="font-weight:600;font-size:.88rem;color:rgba(0,0,0,.6);">
                        {album.get("event_name") or ""}
                    </span>
                </div>
                {_badge("active" if is_active else "inactive")}
            </div>""", unsafe_allow_html=True)

            # Card body
            st.markdown(f"""
            <div style="background:var(--surface);border:1px solid var(--border);
                 border-top:none;border-radius:0 0 12px 12px;padding:.85rem 1rem .7rem;
                 margin-bottom:.2rem;">
                <div style="font-weight:600;font-size:.92rem;color:var(--text);
                     white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                    {album.get("album_name","Unnamed")}
                </div>
                <div style="font-size:.75rem;color:var(--muted);margin-top:3px;">
                    {album.get("event_date") or "—"}
                    &nbsp;·&nbsp;
                    {album.get("total_photos", 0):,} photos
                    &nbsp;·&nbsp;
                    {_fmt_size(album.get("total_size", 0))}
                </div>
                <div style="font-size:.68rem;color:var(--brand);margin-top:5px;
                     font-family:'DM Mono',monospace;overflow:hidden;text-overflow:ellipsis;
                     white-space:nowrap;">
                    🔗 {share_tok[:28]}…
                </div>
            </div>""", unsafe_allow_html=True)

            # Action buttons
            ac1, ac2 = st.columns(2)
            with ac1:
                if st.button("Open", key=f"open_{a_id}", width="stretch"):
                    _goto("album_detail", active_album=album)
            with ac2:
                tog_label = "Deactivate" if is_active else "Activate"
                if st.button(tog_label, key=f"tog_{a_id}", width="stretch"):
                    with st.spinner("…"):
                        _, e = api_toggle_share(a_id)
                    if e:
                        st.error(e)
                    else:
                        st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ALBUM DETAIL
# ═══════════════════════════════════════════════════════════════════════════════

def page_album_detail():
    album = st.session_state.active_album
    if not album:
        st.warning("No album selected.")
        _goto("dashboard")
        return

    a_id      = album.get("id", "")
    is_active = album.get("is_active", False)
    share_tok = album.get("share_link", "")

    # ── Back + header ─────────────────────────────────────────────────────────
    if st.button("← Dashboard", key="back_to_dash"):
        _goto("dashboard")

    hh1, hh2 = st.columns([3, 1])
    with hh1:
        st.markdown(f"## {album.get('album_name', 'Album')}")
        event_label = album.get("event_name") or ""
        date_label  = album.get("event_date")  or ""
        st.markdown(
            f'<p style="color:var(--muted);margin-top:-.6rem;font-size:.83rem;">'
            f'{event_label}{" · " if event_label and date_label else ""}{date_label}</p>',
            unsafe_allow_html=True,
        )
    with hh2:
        st.markdown(
            f'<div style="text-align:right;padding-top:.3rem;">'
            f'{_badge("active" if is_active else "inactive")}</div>',
            unsafe_allow_html=True,
        )

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Photos",     f"{album.get('total_photos', 0):,}")
    mc2.metric("Size",       _fmt_size(album.get("total_size", 0)))
    mc3.metric("Event date", album.get("event_date") or "—")

    st.markdown("---")

    tab_upload, tab_photos, tab_share = st.tabs([
        "📤  Upload & process",
        "🖼️  View photos",
        "🔗  Share settings",
    ])

    # ════════════════════════════════════
    # TAB 1 – UPLOAD
    # ════════════════════════════════════
    with tab_upload:
        st.markdown("#### Upload photos to this album")
        st.caption(
            "Dropped files land in a temp folder first. "
            "AI detects faces → embeddings → FAISS clustering. "
            "Success → moved to permanent storage. Failure → deleted."
        )

        uploaded_files = st.file_uploader(
            "Select photos",
            type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
            accept_multiple_files=True,
            key="album_uploader",
        )

        if uploaded_files:
            st.markdown(
                f'<p style="font-size:.8rem;color:var(--muted);">'
                f'{len(uploaded_files)} file(s) selected</p>',
                unsafe_allow_html=True,
            )

            if st.button("⬆  Upload & run AI", key="do_upload",
                         width="content"):
                files = []
                for f in uploaded_files:
                    raw = f.read()
                    files.append((f.name, raw, f.type or "image/jpeg"))

                prog = st.progress(0, text="Sending to AI pipeline…")
                with st.spinner("Processing… this can take 10–30 s per image"):
                    data, err = api_upload_photos(a_id, files)
                prog.progress(100, text="Done!")

                if err:
                    st.error(f"Upload error: {err}")
                else:
                    results  = data.get("results", [])
                    n_ok     = sum(1 for r in results if r["status"] == "ok")
                    n_nf     = sum(1 for r in results if r["status"] == "no_face")
                    n_err    = sum(1 for r in results if r["status"] == "error")

                    rc1, rc2, rc3 = st.columns(3)
                    rc1.metric("✓ Faces detected", n_ok)
                    rc2.metric("⚠ No face",        n_nf)
                    rc3.metric("✕ Errors",         n_err)

                    st.markdown("#### Per-file results")
                    for r in results:
                        fcl, fcs, fcr = st.columns([3, 1.2, 2.5])
                        with fcl:
                            st.markdown(
                                f'<span style="font-size:.83rem;color:var(--text);">'
                                f'{r["filename"]}</span>',
                                unsafe_allow_html=True,
                            )
                        with fcs:
                            st.markdown(_badge(r["status"]), unsafe_allow_html=True)
                        with fcr:
                            if r.get("person_id"):
                                st.markdown(
                                    f'<span class="person-chip">'
                                    f'👤 {r["person_id"][:10]}…</span>',
                                    unsafe_allow_html=True,
                                )
                            elif r.get("message"):
                                st.markdown(
                                    f'<span style="font-size:.75rem;color:var(--muted);">'
                                    f'{r["message"]}</span>',
                                    unsafe_allow_html=True,
                                )

                    # Refresh album metadata
                    fresh_albums, _ = api_get_albums()
                    if fresh_albums:
                        updated = next(
                            (a for a in fresh_albums if a["id"] == a_id), None
                        )
                        if updated:
                            st.session_state.active_album = updated

    # ════════════════════════════════════
    # TAB 2 – PHOTOS
    # ════════════════════════════════════
    with tab_photos:
        st.markdown("#### Album photos — grouped by person")

        with st.spinner("Loading gallery…"):
            gallery_data, gerr = api_gallery()

        if gerr:
            st.error(gerr)
            return

        album_g = next(
            (a for a in gallery_data.get("albums", []) if a["album_id"] == a_id),
            None,
        )
        if not album_g:
            st.info("No photos yet. Use the Upload tab to add photos.")
            return

        persons  = album_g.get("persons", [])
        real_p   = [p for p in persons if p["person_id"] != "__no_face__"]
        noface_p = [p for p in persons if p["person_id"] == "__no_face__"]

        total_in_album = sum(p["total_photos"] for p in persons)
        st.markdown(
            f'<p style="font-size:.8rem;color:var(--muted);margin-bottom:.5rem;">'
            f'{len(real_p)} person group(s) · {total_in_album:,} total photos</p>',
            unsafe_allow_html=True,
        )

        for person in real_p:
            pid    = person["person_id"]
            photos = person["photos"]
            label  = (
                f"👤  Person {pid[:12]}…  ·  {len(photos)} photo(s)"
            )
            with st.expander(label, expanded=False):
                gcols = st.columns(4)
                for i, ph in enumerate(photos):
                    with gcols[i % 4]:
                        _show_image_safe(_image_url(ph["img_path"]))

        if noface_p:
            with st.expander(
                f"📷  Photos without face — {noface_p[0]['total_photos']}",
                expanded=False,
            ):
                gcols = st.columns(4)
                for i, ph in enumerate(noface_p[0]["photos"]):
                    with gcols[i % 4]:
                        _show_image_safe(_image_url(ph["img_path"]))

    # ════════════════════════════════════
    # TAB 3 – SHARE
    # ════════════════════════════════════
    with tab_share:
        st.markdown("#### Share link settings")
        st.caption("Control public access to this album.")

        full_link = f"{BASE_URL}/album/share/{share_tok}"
        st.markdown(f"""
        <div class="fl-card">
            <div style="font-size:.72rem;color:var(--muted);margin-bottom:4px;
                 font-weight:500;letter-spacing:.04em;text-transform:uppercase;">
                Public share link
            </div>
            <div style="font-family:'DM Mono',monospace;font-size:.8rem;
                 background:var(--bg);padding:9px 12px;border-radius:8px;
                 color:var(--brand-dark);border:1px solid var(--border);
                 word-break:break-all;">
                {full_link}
            </div>
            <div style="margin-top:.7rem;display:flex;align-items:center;gap:.6rem;">
                {_badge("active" if is_active else "inactive")}
                <span style="font-size:.78rem;color:var(--muted);">
                    {"Anyone with this link can view the album."
                     if is_active
                     else "Sharing is off — link returns 404."}
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            if st.button("🔄  Regenerate link", width="stretch", key="regen_link"):
                with st.spinner("Regenerating…"):
                    d, e = api_generate_share_link(a_id)
                if e:
                    st.error(e)
                else:
                    st.success("✓ New share link generated!")
                    fresh, _ = api_get_albums()
                    if fresh:
                        upd = next((a for a in fresh if a["id"] == a_id), None)
                        if upd:
                            st.session_state.active_album = upd
                    st.rerun()

        with sc2:
            toggle_lbl = (
                "🔴  Deactivate" if is_active else "🟢  Activate"
            )
            if st.button(toggle_lbl, width="stretch", key="toggle_share_btn"):
                with st.spinner("Updating…"):
                    d, e = api_toggle_share(a_id)
                if e:
                    st.error(e)
                else:
                    fresh, _ = api_get_albums()
                    if fresh:
                        upd = next((a for a in fresh if a["id"] == a_id), None)
                        if upd:
                            st.session_state.active_album = upd
                    st.rerun()

        with sc3:
            st.markdown("**Copy link**")
            st.code(full_link, language=None)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: GALLERY
# ═══════════════════════════════════════════════════════════════════════════════

def page_gallery():
    st.markdown("## Gallery")
    st.markdown(
        '<p style="color:var(--muted);margin-top:-.6rem;font-size:.83rem;">'
        "All studio photos across every event, grouped by detected person.</p>",
        unsafe_allow_html=True,
    )

    with st.spinner("Loading gallery…"):
        data, err = api_gallery()

    if err:
        st.error(err)
        return

    all_albums = data.get("albums", [])
    if not all_albums:
        st.info("No albums yet. Create an event and upload photos first.")
        return

    # Flatten: person_id → list of (photo_dict, album_name)
    person_map: dict[str, list] = {}
    for alb in all_albums:
        aname = alb["album_name"]
        for person in alb.get("persons", []):
            pid = person["person_id"]
            person_map.setdefault(pid, [])
            for ph in person.get("photos", []):
                person_map[pid].append((ph, aname))

    real_ids  = [p for p in person_map if p != "__no_face__"]
    noface    = person_map.get("__no_face__", [])

    # ── Stats + search ────────────────────────────────────────────────────────
    gc1, gc2, gc3 = st.columns([2, 1, 1])
    with gc1:
        search = st.text_input(
            "Filter by person ID prefix",
            placeholder="Type person ID prefix to filter…",
            label_visibility="collapsed",
            key="gallery_search",
        )
    with gc2:
        st.metric("Unique persons", len(real_ids))
    with gc3:
        total_all = sum(len(v) for v in person_map.values())
        st.metric("Total photos",   total_all)

    st.markdown("---")

    filtered_real = {
        pid: v for pid, v in person_map.items()
        if pid != "__no_face__"
        and (not search or pid.startswith(search))
    }

    if not filtered_real and not noface:
        st.info("No photos match the filter.")
        return

    # ── Person groups ─────────────────────────────────────────────────────────
    for pid, entries in sorted(
        filtered_real.items(), key=lambda x: -len(x[1])
    ):
        albums_in = list({e[1] for e in entries})
        albums_str = ", ".join(albums_in[:2])
        if len(albums_in) > 2:
            albums_str += f" +{len(albums_in)-2}"
        with st.expander(
            f"👤  {pid[:14]}…  ·  {len(entries)} photo(s)  ·  {albums_str}",
            expanded=False,
        ):
            gcols = st.columns(5)
            for i, (ph, aname) in enumerate(entries):
                with gcols[i % 5]:
                    _show_image_safe(_image_url(ph["img_path"]))
                    st.caption(aname)

    if noface:
        with st.expander(
            f"📷  No face detected — {len(noface)} photo(s)", expanded=False
        ):
            gcols = st.columns(5)
            for i, (ph, aname) in enumerate(noface):
                with gcols[i % 5]:
                    _show_image_safe(_image_url(ph["img_path"]))
                    st.caption(aname)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: FACE SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def page_face_search():
    st.markdown("## Face Search")
    st.markdown(
        '<p style="color:var(--muted);margin-top:-.6rem;font-size:.83rem;">'
        "Upload a selfie or face photo to find all matching images in your studio albums.</p>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1.8])

    # ── LEFT: upload panel ────────────────────────────────────────────────────
    with left:
        st.markdown('<div class="fl-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:1.3rem 0 .9rem;">
            <div style="font-size:2.2rem;margin-bottom:.4rem;">🤳</div>
            <div style="font-weight:600;font-size:.92rem;color:var(--text);">
                Upload face photo</div>
            <div style="font-size:.75rem;color:var(--muted);margin-top:2px;">
                Clear frontal photo works best</div>
        </div>""", unsafe_allow_html=True)

        query_file = st.file_uploader(
            "Choose image",
            type=["jpg", "jpeg", "png", "webp"],
            key="face_search_file",
            label_visibility="collapsed",
        )

        if query_file:
            img_bytes = query_file.read()
            st.image(img_bytes, caption="Query photo", width="stretch")

            if st.button("🔍  Search now", width="stretch", key="do_search"):
                with st.spinner("Running face recognition…"):
                    result, err = api_recognize(img_bytes, query_file.name)
                st.session_state["_face_result"] = (result, err)
                st.rerun()
        else:
            if st.session_state.get("_face_result"):
                if st.button("← New search", key="clear_fs"):
                    st.session_state["_face_result"] = None
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # ── RIGHT: results panel ──────────────────────────────────────────────────
    with right:
        face_result = st.session_state.get("_face_result")

        if not face_result:
            st.markdown("""
            <div class="fl-card" style="text-align:center;padding:3.5rem 1rem;">
                <div style="font-size:2.8rem;margin-bottom:.6rem;">🔍</div>
                <div style="font-weight:600;color:var(--text);">
                    Results appear here</div>
                <div style="font-size:.83rem;color:var(--muted);margin-top:.4rem;">
                    Upload a face photo and click Search.</div>
            </div>""", unsafe_allow_html=True)
            return

        data, err = face_result
        if err:
            st.error(f"Recognition error: {err}")
            return

        person_id = data.get("person_id")
        is_new    = data.get("is_new_person", False)
        score     = data.get("similarity_score")
        matches   = data.get("matched_photos", [])

        # ── Result summary card ───────────────────────────────────────────────
        if is_new or not person_id:
            st.markdown("""
            <div class="fl-card" style="border-left:3px solid var(--amber);">
                <div style="font-weight:600;color:var(--amber);font-size:.95rem;">
                    ⚠ No match found</div>
                <div style="font-size:.82rem;color:var(--muted);margin-top:4px;">
                    This face doesn't match anyone in your studio albums yet.
                    Try uploading more photos or lower the similarity threshold.</div>
            </div>""", unsafe_allow_html=True)
        else:
            pct = f"{score * 100:.1f}%" if score is not None else "—"
            st.markdown(f"""
            <div class="fl-card" style="border-left:3px solid var(--teal);">
                <div style="font-weight:600;color:var(--teal);font-size:.95rem;
                     margin-bottom:.6rem;">✓ Match found</div>
                <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:.68rem;color:var(--muted);font-weight:600;
                             text-transform:uppercase;letter-spacing:.06em;">Person ID</div>
                        <div style="font-family:'DM Mono',monospace;font-size:.8rem;
                             color:var(--text);font-weight:500;margin-top:2px;">
                            {person_id[:20]}…</div>
                    </div>
                    <div>
                        <div style="font-size:.68rem;color:var(--muted);font-weight:600;
                             text-transform:uppercase;letter-spacing:.06em;">Similarity</div>
                        <div style="font-size:1.1rem;font-weight:600;color:var(--teal);
                             margin-top:2px;">{pct}</div>
                    </div>
                    <div>
                        <div style="font-size:.68rem;color:var(--muted);font-weight:600;
                             text-transform:uppercase;letter-spacing:.06em;">Photos found</div>
                        <div style="font-size:1.1rem;font-weight:600;color:var(--text);
                             margin-top:2px;">{len(matches)}</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            if matches:
                st.markdown("#### Matched photos")
                gcols = st.columns(4)
                for i, ph in enumerate(matches):
                    with gcols[i % 4]:
                        _show_image_safe(_image_url(ph["img_path"]))
                        st.caption(
                            f"{ph['album_name']}\n"
                            f"sim: {ph.get('similarity', 0):.3f}"
                        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: PUBLIC SHARE VIEW
# ═══════════════════════════════════════════════════════════════════════════════

def page_share_view():
    token = (st.session_state.get("share_token") or "").strip()
    if not token:
        st.warning("No share token provided.")
        if st.button("← Go to login"):
            _goto("login")
        return

    with st.spinner("Loading shared album…"):
        data, err = api_share_album(token)

    if err:
        st.markdown("""
        <div class="fl-card" style="text-align:center;padding:3.5rem 1rem;
             max-width:480px;margin:4rem auto;">
            <div style="font-size:3rem;margin-bottom:.7rem;">🔒</div>
            <div style="font-weight:600;font-size:1.05rem;color:var(--text);">
                Album not available</div>
            <div style="font-size:.83rem;color:var(--muted);margin-top:.4rem;">
                This link may be invalid or the studio has disabled sharing.</div>
        </div>""", unsafe_allow_html=True)
        st.error(err)
        if st.button("← Back"):
            _goto("dashboard" if _is_logged_in() else "login")
        return

    # ── Album header ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="fl-card" style="border-left:4px solid var(--brand);margin-bottom:1.2rem;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:.3rem;">
            <div style="width:8px;height:8px;border-radius:50%;
                 background:var(--brand);"></div>
            <span style="font-size:.72rem;color:var(--brand);font-weight:600;
                 letter-spacing:.04em;text-transform:uppercase;">
                Shared album · FaceLinkAI Studio</span>
        </div>
        <div style="font-size:1.3rem;font-weight:600;color:var(--text);">
            {data.get("album_name","Album")}</div>
        <div style="font-size:.8rem;color:var(--muted);margin-top:3px;">
            {data.get("event_name") or ""}
            {" · " if data.get("event_name") and data.get("event_date") else ""}
            {data.get("event_date") or ""}
            &nbsp;·&nbsp;
            {data.get("total_photos", 0):,} photos
        </div>
    </div>""", unsafe_allow_html=True)

    photos = data.get("photos", [])
    if not photos:
        st.info("This album has no photos yet.")
        return

    # Group by person_id
    person_map: dict[str, list] = {}
    for ph in photos:
        pid = ph.get("person_id") or "__no_face__"
        person_map.setdefault(pid, []).append(ph)

    # ── Selfie search panel ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🤳  Find MY photos — upload a selfie", expanded=True):
        sf1, sf2 = st.columns([1, 2])
        with sf1:
            selfie = st.file_uploader(
                "Upload your photo",
                type=["jpg", "jpeg", "png", "webp"],
                key="pub_selfie_file",
            )
            if selfie:
                st.image(selfie.read(), width="stretch")
        with sf2:
            st.markdown("""
            <div style="padding:1rem 0;">
                <div style="font-weight:600;font-size:.9rem;color:var(--text);
                     margin-bottom:.4rem;">How it works</div>
                <div style="font-size:.82rem;color:var(--muted);line-height:1.6;">
                    1. Upload a clear selfie<br>
                    2. Our AI matches your face to photos in the album<br>
                    3. Only your photos are shown<br><br>
                    <em>Full face search requires a studio-issued recognition link.</em>
                </div>
            </div>""", unsafe_allow_html=True)
            if selfie:
                st.info(
                    "Face recognition on public share pages requires a studio-issued "
                    "direct link. Contact the studio for personalised access."
                )

    # ── Photos grouped by person ──────────────────────────────────────────────
    st.markdown("### Photos in this album")

    real  = {pid: phs for pid, phs in person_map.items() if pid != "__no_face__"}
    nfphs = person_map.get("__no_face__", [])

    for pid, phs in sorted(real.items(), key=lambda x: -len(x[1])):
        with st.expander(f"👤  Person group — {len(phs)} photo(s)", expanded=False):
            gcols = st.columns(4)
            for i, ph in enumerate(phs):
                with gcols[i % 4]:
                    _show_image_safe(_image_url(ph["img_path"]))

    if nfphs:
        with st.expander(f"📷  Other photos — {len(nfphs)}", expanded=False):
            gcols = st.columns(4)
            for i, ph in enumerate(nfphs):
                with gcols[i % 4]:
                    _show_image_safe(_image_url(ph["img_path"]))

    st.markdown("---")
    if st.button("← Back"):
        _goto("dashboard" if _is_logged_in() else "login")


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

_render_sidebar()

_page = st.session_state.page

# Public pages (no auth needed)
if _page == "login":
    page_login()
elif _page == "register":
    page_register()
elif _page == "share_view":
    page_share_view()

# Auth guard
elif not _is_logged_in():
    st.warning("Please log in to continue.")
    page_login()

# Protected pages
elif _page == "dashboard":
    page_dashboard()
elif _page == "album_detail":
    page_album_detail()
elif _page == "gallery":
    page_gallery()
elif _page == "face_search":
    page_face_search()
else:
    page_dashboard()