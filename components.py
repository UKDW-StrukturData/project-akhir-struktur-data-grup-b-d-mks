

import streamlit as st
import json
import csv
from io import StringIO
from config import POPULAR_QUERIES

def show_popular_movies():
    """Menampilkan film-film populer sebagai quick access"""
    st.subheader("Film Populer")
    
    cols = st.columns(5)
    for idx, movie in enumerate(POPULAR_QUERIES):
        with cols[idx]:
            if st.button(f"{movie}", use_container_width=True):
                st.session_state.page = "search"
                st.session_state.last_query = movie
                st.rerun()

def show_import_export():
    """Menampilkan fitur Import/Export"""
    st.subheader("📁 Import & Export Data")
    
    col_import, col_export = st.columns(2)
    
    with col_import:
        show_import_section()
    
    with col_export:
        show_export_section()

def show_import_section():
    """Komponen untuk import data"""
    st.markdown("### 📥 Import Data")
    uploaded_file = st.file_uploader(
        "Unggah file JSON/CSV", 
        type=['json', 'csv'],
        help="Unggah file hasil export sebelumnya"
    )
    
    if uploaded_file is not None:
        handle_file_upload(uploaded_file)

def handle_file_upload(uploaded_file):
    """Handle uploaded file"""
    try:
        if uploaded_file.type == "application/json":
            imported_data = json.load(uploaded_file)
            st.success(f"✅ Berhasil import {len(imported_data)} film dari JSON!")
            
            if st.button("📋 Lihat Data Import"):
                st.session_state.imported_data = imported_data
                st.session_state.page = "import_view"
                st.rerun()
                
        elif uploaded_file.type == "text/csv":
            # Read CSV file
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            imported_data = []
            csv_reader = csv.DictReader(stringio)
            for row in csv_reader:
                imported_data.append(row)
            
            st.success(f"✅ Berhasil import {len(imported_data)} film dari CSV!")
            
            if st.button("📋 Lihat Data Import"):
                st.session_state.imported_data = imported_data
                st.session_state.page = "import_view"
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Error importing file: {str(e)}")

def show_export_section():
    """Komponen untuk export data"""
    st.markdown("### 📤 Export Data")
    st.info("Fitur export tersedia setelah melakukan pencarian film")
    
    # Contoh template untuk download
    st.download_button(
        label="📄 Download Template CSV",
        data="title,year,runtime,jwRating,tomatometer\nAvengers,2012,143,0.95,92\n",
        file_name="template_film.csv",
        mime="text/csv"
    )

def show_search_history():
    """Menampilkan history pencarian"""
    if st.session_state.search_history:
        with st.expander("📚 History Pencarian Terakhir"):
            hist_cols = st.columns(3)
            for idx, hist in enumerate(reversed(st.session_state.search_history[-3:])):
                with hist_cols[idx]:
                    if st.button(f"{hist}", use_container_width=True):
                        st.session_state.last_query = hist
                        st.rerun()

def show_movie_card(item, col):
    """Menampilkan kartu film individual"""
    with col:
        title = item.get("title") or "—"
        year = item.get("year") or ""
        runtime = item.get("runtime") or ""
        jwRating = item.get("jwRating") or ""
        tomatometer = item.get("tomatometer") or ""
        tomatocertifiedFresh = item.get("tomatocertifiedFresh") or False
        overview = item.get("overview") or ""
        poster = item.get("poster") or ""
        link = item.get("link") or ""
        offers = item.get("offers") or []

        # Tampilkan poster
        show_poster(poster)

        # Judul dan tahun
        st.markdown(f"**{title}** {f'({year})' if year else ''}")

        # Tombol favorit
        show_favorite_button(title, year)

        # Metrics rating
        show_movie_metrics(jwRating, tomatometer, tomatocertifiedFresh, runtime)

        # Deskripsi
        if overview:
            st.caption(overview if len(overview) < 150 else overview[:147] + "...")

        # Streaming availability
        show_streaming_offers(offers)

        # Link detail
        if link:
            st.markdown(f"[📖 Lihat detail]({link})")

def show_poster(poster):
    """Menampilkan poster film"""
    if poster:
        try:
            st.image(poster, use_container_width=True)
        except Exception as e:
            st.error("❌ Gambar tidak dapat dimuat")
    else:
        st.info("Poster tidak tersedia")

def show_favorite_button(title, year):
    """Tombol favorit"""
    movie_id = f"{title}_{year}"
    is_favorite = movie_id in st.session_state.favorites
    
    col_fav, col_space = st.columns([1, 5])
    with col_fav:
        if st.button("❤️" if is_favorite else "🤍", key=f"fav_{movie_id}"):
            if movie_id in st.session_state.favorites:
                st.session_state.favorites.remove(movie_id)
            else:
                st.session_state.favorites.append(movie_id)
            st.rerun()

def show_movie_metrics(jwRating, tomatometer, tomatocertifiedFresh, runtime):
    """Menampilkan metrics film"""
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        if jwRating:
            if isinstance(jwRating, (int, float)):
                st.metric("⭐ Rating", f"{jwRating:.1%}", label_visibility="collapsed")
    
    with metric_cols[1]:
        if tomatometer:
            certified = " if tomatocertifiedFresh else "
            st.metric(f"{tomatometer}%", label_visibility="collapsed")
    
    with metric_cols[2]:
        if runtime:
            if isinstance(runtime, int):
                st.metric("⏱️", f"{runtime}m", label_visibility="collapsed")

def show_streaming_offers(offers):
    """Menampilkan daftar streaming availability"""
    if offers:
        with st.expander(f"🎬 Tersedia di ({len(offers)})"):
            for offer in offers[:3]:
                offer_name = offer.get("name") or ""
                offer_type = offer.get("type") or ""
                offer_url = offer.get("url") or ""
                
                if offer_name:
                    if offer_url:
                        st.markdown(f"**{offer_name}** ({offer_type}) - [Tonton]({offer_url})")
                    else:
                        st.markdown(f"**{offer_name}** ({offer_type})")
