import streamlit as st
import requests
import os

st.set_page_config(page_title="FaceLinkAI", layout="wide")

# --- HEADER ---
st.title("FaceLinkAI - AI Face Recognition System")
st.write("Upload images → Bulk Register, Recognize, or Cluster")

API_URL = "http://127.0.0.1:8000"

# --- SIDEBAR ---

menu = st.sidebar.selectbox("Menu", ["Home", "Register Faces (Bulk)", "Recognize Face", "Run Clustering", "View Gallery"])
# ---------------- HOME ----------------
if menu == "Home":
    st.subheader("Welcome !")
    st.info("System Capabilities:\n- Bulk Registration\n- Auto-Deduplication\n- Smart Clustering & Merging")

# ---------------- REGISTER (BULK) ----------------
elif menu == "Register Faces (Bulk)":
    st.subheader("📌 Register Faces in Bulk")

    # Optional Name
    name = st.text_input("Enter Name (Optional - leave blank for auto-generate)")
    
    # accept_multiple_files=True allows 100+ photos
    uploaded_files = st.file_uploader("Upload Face Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if uploaded_files:
        st.write(f"Total Photos Selected: {len(uploaded_files)}")
        
        if st.button("Register All"):
            with st.spinner("Registering... please wait"):
                # Backend ko List[UploadFile] format mein bhej rahe hain
                files = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
                data = {"name": name} if name else {}

                response = requests.post(f"{API_URL}/register-face", files=files, data=data)
                
                if response.status_code == 200:
                    res_data = response.json()
                    st.success(f"Processed {len(uploaded_files)} files!")
                    # Detailed results (kounsa success hua kounsa fail)
                    with st.expander("View Detailed Status"):
                        st.json(res_data)
                else:
                    st.error(f"Error: {response.text}")

# ---------------- RECOGNIZE ----------------
elif menu == "Recognize Face":
    st.subheader("🔍 Recognize Face")

    file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    if file:
        st.image(file, caption="Preview", width=250)

        if st.button("Recognize"):
            files = {"file": (file.name, file.getvalue(), file.type)}
            response = requests.post(f"{API_URL}/recognize-face", files=files)

            if response.status_code == 200:
                result = response.json().get("result", [])

                if not result:
                    st.warning("Photo mein koi chehra nahi mila.")
                
                for person in result:
                    is_new = "🆕" if person.get("status") == "new" else "👤"
                    st.subheader(f"{is_new} {person['person']}")
                    
                    # History of photos
                    images = person.get("images", [])
                    if images:
                        cols = st.columns(4)
                        for idx, img_path in enumerate(images):
                            with cols[idx % 4]:
                                full_url = f"{API_URL}/{img_path}"
                                st.image(full_url, width="stretch")
                    else:
                        st.info("No linked photos found.")
                    st.divider() 
            else:
                st.error("API error or face not found.")

# ---------------- CLUSTERING ----------------
elif menu == "Run Clustering":
    st.subheader("🧩 Smart Clustering Engine")

    if st.button("Start Clustering & Merging"):
        with st.spinner("Analyzing database... this might take a while"):
            response = requests.get(f"{API_URL}/run-clustering")
            
            if response.status_code == 200:
                res = response.json()
                st.success("Clustering Done!")
                st.metric("Clusters Found", res.get("total_clusters", 0))
                st.metric("Records Merged", res.get("records_updated", 0))
                st.write(f"Groups Managed: {res.get('groups_merged', 0)}")
            else:
                st.error("Clustering failed. Check if you have data in database.")
elif menu == "View Gallery":
    st.header("🖼️ Database Gallery")
    
    response = requests.get(f"{API_URL}/get-gallery")
    
    if response.status_code == 200:
        data = response.json()
        gallery = data.get("gallery", [])
        
        if not gallery:
            st.warning("Gallery khali hai. Pehle photos register karein.")
        else:
            st.write(f"Total Photos in DB: {data['total']}")
            
            # Search/Filter by Name
            search_query = st.text_input("Filter by Name", "").lower()
            filtered_gallery = [item for item in gallery if search_query in item['name'].lower()]
            
            # Display in Grid
            cols = st.columns(4) # 4 images per row
            for idx, item in enumerate(filtered_gallery):
                with cols[idx % 4]:
                    full_url = f"{API_URL}/{item['image']}"
                    st.image(full_url, caption=item['name'], width="stretch")
                    # Optional: Unique ID ya Path dikhane ke liye
                    st.caption(f"Path: {item['image'].split('/')[-1]}")
    else:
        st.error("Gallery load nahi ho payi.")