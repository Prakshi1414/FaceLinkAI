import streamlit as st
import requests
from PIL import Image

st.set_page_config(page_title="FaceLinkAI", layout="centered")

st.title("FaceLinkAI - AI Face Recognition System")
st.write("Upload image → Register or Recognize face")

API_URL = "http://127.0.0.1:8000"

menu = st.sidebar.selectbox("Menu", ["Home", "Register Face", "Recognize Face"])

# ---------------- HOME ----------------
if menu == "Home":
    st.subheader("Welcome !")
    st.info("This system uses DeepFace + FastAPI + Folder Database")

# ---------------- REGISTER ----------------
elif menu == "Register Face":
    st.subheader("📌 Register New Face")

    name = st.text_input("Enter Name")

    file = st.file_uploader("Upload Face Image", type=["jpg", "png", "jpeg"])

    if file and name:
        st.image(file, caption="Preview", width=250)

        if st.button("Register"):
            files = {"file": file.getvalue()}
            data = {"name": name}

            response = requests.post(
                f"{API_URL}/register-face",
                files={"file": file},
                data=data
            )

            st.success(response.json()["message"])

# ---------------- RECOGNIZE ----------------
elif menu == "Recognize Face":
    st.subheader("🔍 Recognize Face")

    file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    if file:
        st.image(file, caption="Preview", width=250)

        if st.button("Recognize"):
            response = requests.post(
                f"{API_URL}/recognize-face",
                files={"file": file}
            )

            result = response.json()["result"]

            # Recognize section mein is loop ko use karein
            for person in result:
                st.subheader(f"👤 {person['person']}")
                
                # Photos ko 3 columns mein dikhane ke liye
                cols = st.columns(3)
                for idx, img_path in enumerate(person["images"]):
                    with cols[idx % 3]:
                        # Agar StaticFiles mount kiya hai toh API_URL use karein
                        full_url = f"{API_URL}/{img_path}" if not img_path.startswith("http") else img_path
                        st.image(full_url, use_container_width=True)