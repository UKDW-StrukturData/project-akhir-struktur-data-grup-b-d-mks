import streamlit as st
from config import initialize_session_state
from pages import show_start_page, show_search_page, show_import_view

# Setup page config
st.set_page_config(
    page_title="Movie Recommender",
    layout="wide",
    page_icon="🎬"
)

# Initialize session state
initialize_session_state()

# -------- Sidebar Menu --------
st.sidebar.title("Navigasi")

menu = st.sidebar.radio(
    "Pilih Halaman:",
    ["Beranda", "Pencarian", "Impor / Ekspor Data"]
)

# -------- Routing Halaman --------
if menu == "Beranda":
    show_start_page()

elif menu == "Pencarian":
    show_search_page()

elif menu == "Impor / Ekspor Data":
    show_import_view()

else:
    show_start_page()
