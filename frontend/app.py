import streamlit as st
import requests
from PIL import Image

st.set_page_config(page_title="FaceLinkAI", layout="centered")

# --- HEADER ---
st.title("FaceLinkAI - AI Face Recognition System")
st.write("Upload image → Register or Recognize face")

API_URL = "http://127.0.0.1:8000"

# --- SIDEBAR ---
menu = st.sidebar.selectbox("Menu", ["Home", "Register Face", "Recognize Face"])

# ---------------- HOME ----------------
if menu == "Home":
    st.subheader("Welcome !")
    st.info("This system uses DeepFace + FastAPI + Folder Database")
    st.markdown("""
    - **Register:** Apni photos ko naam ke saath save karein.
    - **Recognize:** Photo upload karein aur system purane records se match dhoondega.
    """)

# ---------------- REGISTER ----------------
elif menu == "Register Face":
    st.subheader("📌 Register New Face")

    name = st.text_input("Enter Name")
    file = st.file_uploader("Upload Face Image", type=["jpg", "png", "jpeg"])

    if file and name:
        st.image(file, caption="Preview", width=250)

        if st.button("Register"):
          
            files = {"file": (file.name, file.getvalue(), file.type)}
            data = {"name": name}

            response = requests.post(f"{API_URL}/register-face", files=files, data=data)
            
            if response.status_code == 200:
                st.success(response.json()["message"])
            else:
                st.error("Registration fail ho gaya. Backend check karein.")

# ---------------- RECOGNIZE ----------------
elif menu == "Recognize Face":
    st.subheader("🔍 Recognize Face")

    file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    if file:
        st.image(file, caption="Preview", width=250)

        if st.button("Recognize"):
            # Recognize request
            files = {"file": (file.name, file.getvalue(), file.type)}
            response = requests.post(f"{API_URL}/recognize-face", files=files)

            if response.status_code == 200:
                result = response.json()["result"]

                if not result:
                    st.warning("Photo mein koi chehra nahi mila.")
                
                for person in result:
                 
                    is_new = "🆕" if person.get("status") == "new" else "👤"
                    st.subheader(f"{is_new} {person['person']}")
                    
               
                    images = person.get("images", [])
                    if images:
                        cols = st.columns(3)
                        for idx, img_path in enumerate(images):
                            with cols[idx % 3]:
                                # URL handling for Static Files
                                full_url = f"{API_URL}/{img_path}" if not img_path.startswith("http") else img_path
                                st.image(full_url, width='stretch')
                    else:
                        st.info("Is person ki koi linked photos nahi mili.")
                    
                    st.divider() 
            else:
                st.error("API se connect nahi ho pa raha.")