# config.py
# Konfigurasi dan session state management

import streamlit as st

def initialize_session_state():
    """Inisialisasi session state"""
    if "page" not in st.session_state:
        st.session_state.page = "start"
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    if "favorites" not in st.session_state:
        st.session_state.favorites = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "imported_data" not in st.session_state:
        st.session_state.imported_data = []
    if "last_query" not in st.session_state:
        st.session_state.last_query = ""

# Konstanta
POPULAR_QUERIES = ["Avengers", "Spider Man", "Batman", "Avatar", "Iron Man"]