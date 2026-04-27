import streamlit as st
import requests

# =========================
# CONFIG
# =========================
BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="FaceLinkAI", layout="wide")

# =========================
# API HELPERS
# =========================
def post(endpoint, data=None, headers=None, files=None):
    return requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers, files=files)

def get(endpoint, headers=None):
    return requests.get(f"{BASE_URL}{endpoint}", headers=headers)

def auth_headers():
    if "token" in st.session_state and st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

# =========================
# SESSION INIT
# =========================
if "token" not in st.session_state:
    st.session_state.token = None


# =========================
# SIDEBAR UI
# =========================
st.sidebar.title("📸 FaceLinkAI")
menu = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📝 Register", "🔐 Login", "📊 Dashboard", "📁 Albums", "⬆️ Upload Photos", "🔗 Share Links", "🌐 Public Album", "👥 Gallery"]
)

st.sidebar.markdown("---")
if st.session_state.token:
    st.sidebar.success("Logged In ✔")
else:
    st.sidebar.warning("Not Logged In ❌")


# =========================
# HOME
# =========================
if menu == "🏠 Home":
    st.title("FaceLinkAI 🚀")
    st.subheader("AI Powered Face Recognition Album System")

    col1, col2, col3 = st.columns(3)
    col1.metric("Albums", "AI Powered")
    col2.metric("Face Detection", "Deep Learning")
    col3.metric("Sharing", "Public Links")

    st.info("Login to manage albums, upload photos, and generate smart face-based galleries.")


# =========================
# REGISTER
# =========================
elif menu == "📝 Register":
    st.title("Create Account")

    with st.form("register_form"):
        studio_name = st.text_input("Studio Name")
        mobile = st.text_input("Mobile Number")
        email = st.text_input("Email (optional)")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Register")

        if submitted:
            res = post("/register-user", {
                "studio_name": studio_name,
                "mobile_number": mobile,
                "email": email,
                "username": username,
                "password": password
            })

            if res.status_code == 201:
                st.success("Registration Successful 🎉")
            else:
                st.error(res.text)


# =========================
# LOGIN
# =========================
elif menu == "🔐 Login":
    st.title("Login")

    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = post("/login-user", {
            "mobile_number": mobile,
            "password": password
        })

        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data["access_token"]
            st.success("Login Successful 🎉")
        else:
            st.error("Invalid credentials")


# =========================
# DASHBOARD
# =========================
elif menu == "📊 Dashboard":
    st.title("Dashboard")

    if not st.session_state.token:
        st.warning("Please login first")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("Status", "Active")
    col2.metric("System", "FaceLinkAI")
    col3.metric("Mode", "AI Recognition")

    st.success("Welcome to your Smart Photo Management System 🚀")


# =========================
# ALBUMS
# =========================
elif menu == "📁 Albums":
    st.title("Album Management")

    if not st.session_state.token:
        st.warning("Login required")
        st.stop()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Create Album")
        name = st.text_input("Album Name")
        date = st.date_input("Event Date")

        if st.button("Create"):
            res = post("/create-album", {
                "album_name": name,
                "event_date": str(date)
            }, headers=auth_headers())

            st.write(res.json())

    with col2:
        st.subheader("All Albums")

        if st.button("Load Albums"):
            res = get("/get-albums", headers=auth_headers())
            st.write(res.json())


# =========================
# UPLOAD
# =========================
elif menu == "⬆️ Upload Photos":
    st.title("Upload Photos")

    if not st.session_state.token:
        st.warning("Login required")
        st.stop()

    album_id = st.text_input("Album ID")
    files = st.file_uploader("Select Images", accept_multiple_files=True)

    if st.button("Upload"):
        if files:
            for f in files:
                res = post(
                    f"/album/{album_id}/upload-album-photos",
                    files={"file": (f.name, f, f.type)},
                    headers=auth_headers()
                )
                st.write(res.json())
        else:
            st.warning("Select images first")


# =========================
# SHARE LINKS
# =========================
elif menu == "🔗 Share Links":
    st.title("Share Management")

    if not st.session_state.token:
        st.warning("Login required")
        st.stop()

    album_id = st.text_input("Album ID")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Generate Link"):
            res = post(f"/album/{album_id}/generate-share-link", headers=auth_headers())
            st.success(res.json())

    with col2:
        if st.button("Toggle Link"):
            res = post(f"/album/{album_id}/toggle-share", headers=auth_headers())
            st.warning(res.json())


# =========================
# PUBLIC ALBUM
# =========================
elif menu == "🌐 Public Album":
    st.title("Public Album Viewer")

    share_link = st.text_input("Enter Share Link")

    if st.button("Open Album"):
        res = get(f"/album/share/{share_link}")
        st.write(res.json())


# =========================
# GALLERY
# =========================
elif menu == "👥 Gallery":
    st.title("Smart Gallery")

    if not st.session_state.token:
        st.warning("Login required")
        st.stop()

    if st.button("Load Gallery"):
        res = get("/gallery", headers=auth_headers())
        st.write(res.json())