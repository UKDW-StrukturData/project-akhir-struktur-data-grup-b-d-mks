import streamlit as st
from config import initialize_session_state
from pages import show_start_page, show_search_page, show_import_view

# Setup page config
st.set_page_config(
    page_title="Cari Film (API IMDb/JustWatch)",
    layout="wide",
    page_icon="🎬"
)

# Initialize session state
initialize_session_state()

# -------- Sidebar Menu --------
st.sidebar.title("📂 Navigasi")

menu = st.sidebar.radio(
    "Pilih Halaman:",
    ("Beranda", "Pencarian Film", "Import & Export Data")
)

# Simpan pilihan ke session_state agar konsisten
if menu == "Beranda":
    st.session_state.page = "start"

elif menu == "Pencarian Film":
    st.session_state.page = "search"

elif menu == "Import & Export Data":
    st.session_state.page = "import_view"


# -------- Routing Halaman --------
if st.session_state.page == "start":
    show_start_page()

elif st.session_state.page == "search":
    show_search_page()

elif st.session_state.page == "import_view":
    show_import_view()

else:
    show_start_page()
