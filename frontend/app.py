
import streamlit as st
import requests
import os
 
st.set_page_config(page_title="FaceLinkAI", layout="wide")
 
API_URL = "http://127.0.0.1:8000"
 
st.title("FaceLinkAI – AI Face Recognition System")
st.caption("Bulk Register · Recognize · Gallery · Auto-Deduplication")
 
menu = st.sidebar.selectbox(
    "Navigation",
    ["🏠 Home", "📌 Register Faces", "🔍 Recognize Face", "🖼️ Gallery"]
)
 
# ── HOME ──────────────────────────────────────────────────────────────────────
if menu == "🏠 Home":
    st.subheader("Welcome!")
    st.info(
        "**System Capabilities**\n"
        "- Bulk image registration (single + group photos)\n"
        "- Auto deduplication via centroid merging\n"
        "- Cosine similarity search (Facenet512 + FAISS)\n"
        "- Group image support (RetinaFace detector)\n"
        "- Gallery: grid view + group-by-person view"
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View System Stats"):
            r = requests.get(f"{API_URL}/stats")
            if r.status_code == 200:
                s = r.json()
                st.metric("total embeddings", s["total_embeddings"])
                st.metric("Unique Persons",   s["total_persons"])
                st.json(s["persons"])
            else:
                st.error("Could not fetch stats.")
 
# ── REGISTER ──────────────────────────────────────────────────────────────────
elif menu == "📌 Register Faces":
    st.subheader("Register Faces (Bulk)")
    st.info(
        "💡 **Tip**: If all uploaded images are of the **same person**, enter their name. "
        "For mixed/group images, leave the name blank – identities are auto-detected."
    )
 
    name           = st.text_input("Person Name (optional – leave blank for mixed/group uploads)")
    uploaded_files = st.file_uploader(
        "Upload images", type=["jpg", "jpeg", "png"], accept_multiple_files=True
    )
 
    if uploaded_files:
        st.write(f"**{len(uploaded_files)}** file(s) selected.")
 
        if st.button("Register All"):
            with st.spinner("Registering… this may take a moment for large batches."):
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files
                ]
                data = {"name": name} if name.strip() else {}
                response = requests.post(
                    f"{API_URL}/register-face", files=files_payload, data=data
                )
 
            if response.status_code == 200:
                res = response.json()
                st.success(f"✅ Processed {res['processed']} file(s).")
 
                success = [d for d in res["details"] if d.get("status") == "added"]
                skipped = [d for d in res["details"] if d.get("status") != "added"]
 
                st.write(f"**Added:** {len(success)} &nbsp; **Skipped/No-face:** {len(skipped)}")
 
                with st.expander("See full details"):
                    st.json(res["details"])
            else:
                st.error(f"Registration failed:\n```\n{response.text}\n```")
 
# ── RECOGNIZE ─────────────────────────────────────────────────────────────────
elif menu == "🔍 Recognize Face":
    st.subheader("Recognize Face")
    file = st.file_uploader("Upload image (single or group)", type=["jpg", "jpeg", "png"])
 
    if file:
        st.image(file, caption="Uploaded image", width=300)
 
        if st.button("Recognize"):
            with st.spinner("Analyzing…"):
                response = requests.post(
                    f"{API_URL}/recognize-face",
                    files={"file": (file.name, file.getvalue(), file.type)}
                )
 
            if response.status_code == 200:
                results = response.json().get("result", [])
 
                if not results:
                    st.warning("No faces detected in this image.")
                else:
                    st.write(f"**{len(results)} face(s) detected:**")
 
                for person in results:
                    status = person.get("status", "")
                    score  = person.get("score", 0.0)
                    label  = "🆕 New" if status == "new" else "👤 Known"
 
                    with st.container():
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            st.subheader(f"{label}: {person['person']}")
                        with col_b:
                            st.metric("Confidence", f"{score:.2%}")   # FIX 3
 
                        imgs = person.get("images", [])
                        if imgs:
                            cols = st.columns(min(4, len(imgs)))
                            for i, img_path in enumerate(imgs[:8]):   # max 8 shown
                                with cols[i % 4]:
                                    st.image(f"{API_URL}/{img_path}", width="stretch")
                        else:
                            st.info("No linked photos yet.")
                        st.divider()
            else:
                st.error(f"API error: {response.text}")
 
# ── GALLERY ───────────────────────────────────────────────────────────────────
elif menu == "🖼️ Gallery":
    st.header("Database Gallery")
 
    # FIX 4: merge trigger in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🔄 Merge Duplicate Identities"):
            with st.spinner("Merging…"):
                r = requests.post(f"{API_URL}/merge-duplicates")
            if r.status_code == 200:
                st.success("Merge complete! Refresh gallery.")
            else:
                st.error("Merge failed.")
 
    response = requests.get(f"{API_URL}/get-gallery")
 
    if response.status_code != 200:
        st.error("Could not fetch gallery.")
        st.stop()
 
    data    = response.json()
    gallery = data.get("gallery", [])
 
    if not gallery:
        st.warning("Gallery is empty. Register some faces first!")
        st.stop()
 
    st.write(f"**Total entries:** {data['total']}")
 
    view_mode = st.radio("Display Mode", ["Grid View", "Group by Person"], horizontal=True)
 
    if view_mode == "Grid View":
        search = st.text_input("Filter by name", "").strip().lower()
        items  = [g for g in gallery if search in g["name"].lower()]
 
        cols = st.columns(4)
        for i, item in enumerate(items):
            with cols[i % 4]:
                st.image(f"{API_URL}/{item['image']}", width="stretch")
                st.caption(item["name"])   # FIX 1
 
    else:
        unique_names = sorted(set(g["name"] for g in gallery))
        st.write(f"**{len(unique_names)} unique person(s) in DB**")
 
        for person_name in unique_names:
            photos = [g for g in gallery if g["name"] == person_name]
            with st.expander(f"👤 {person_name}  ({len(photos)} photo(s))"):
                inner_cols = st.columns(5)
                for i, photo in enumerate(photos):
                    with inner_cols[i % 5]:
                        st.image(f"{API_URL}/{photo['image']}",width="stretch")
                        st.caption(photo["image"].split("/")[-1])
 