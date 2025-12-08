import streamlit as st
import requests
import json
import csv
import pandas as pd
import typing_extensions as typing
import google.generativeai as genai
import math
import plotly.express as px
from io import StringIO
from urllib.parse import quote_plus
from datetime import datetime


# =================KONFIGURASI=================
# Masukkan API KEY Gemini kamu di sini
GEMINI_API_KEY = "AIzaSyDrm6kAarnzmYfHEmFeFWN-dPffmGRRslk"

st.set_page_config(page_title="Cari Film & Rekomendasi AI", layout="wide", page_icon="🎬")

# Session state untuk navigasi dan data
if "page" not in st.session_state:
    st.session_state.page = "start"
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "imported_data" not in st.session_state:
    st.session_state.imported_data = []

# =================GEMINI AI SETUP=================

# 1. Definisikan Struktur Data (Schema) untuk Output Gemini
class MovieRecommendation(typing.TypedDict):
    judul_film: str
    imdb_rating: float
    image_url: str

# 2. Fungsi Helper Gemini untuk Rekomendasi
def get_movie_recommendations(movie_title: str):
    """
    Meminta rekomendasi film serupa dari Gemini API dalam format JSON.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "GANTI_DENGAN_API_KEY_DISINI":
        return {"error": "API Key Gemini belum diatur atau masih default."}

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Menggunakan Schema agar output PASTI JSON yang valid
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": list[MovieRecommendation]
            }
        )

        prompt = f"""
        Bertindaklah sebagai ahli film dan rekomendasi movie.
        Tugas: Berikan 6 rekomendasi film yang sangat mirip atau relevan dengan film '{movie_title}' berdasarkan data IMDb.
        
        Untuk setiap film, berikan:
        1. judul_film: Judul lengkap film.
        2. imdb_rating: Rating IMDb (float).
        3. image_url: URL poster film yang valid (cari poster paling ikonik/umum).
        """

        response = model.generate_content(prompt)
        return json.loads(response.text)

    except Exception as e:
        return {"error": f"Gagal menghubungi Gemini: {str(e)}"}

# 3. Fungsi Helper Gemini untuk Deskripsi
def get_movie_description(movie_title: str):
    """
    Meminta Gemini untuk membuat deskripsi singkat tentang film jika data API kosong.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "GANTI_DENGAN_API_KEY_DISINI":
        return None

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Gunakan model tanpa schema JSON karena kita hanya butuh teks
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f"""
        Tugas: Berikan deskripsi plot atau sebuah sipnosis yang singkat dan menarik (maksimal 5 paragraf) untuk film '{movie_title}'. Fokus pada premis utama tanpa membocorkan akhir cerita (spoiler).
        """

        response = model.generate_content(prompt)
        return response.text

    except Exception:
        return None
    
# FUNGSI get_imdb_rating DIHAPUS SESUAI PERMINTAAN

# =================HALAMAN-HALAMAN=================

def show_start_page():
    st.title("🎬 Pencarian Film")
    st.markdown("Cari info film lengkap dengan sekali klik!")
    
    # Tampilkan film populer
    show_popular_movies()
    
    # Fitur Import/Export di halaman awal
    show_import_export()
    
    st.markdown("---")
    
    st.subheader("Cara Menggunakan:")
    st.markdown("""
    1. *Klik tombol 'Mulai Cari Film'* di bawah
    2. *Masukkan nama film* yang ingin dicari
    3. *Pilih Film:* Klik tombol "Lihat Detail" pada film yang diinginkan.
    4. *Dapatkan Rekomendasi:* AI akan otomatis mencarikan film serupa di halaman detail.
    """)
    
    st.markdown("---")
    
    if st.button("🚀 Mulai Cari Film", type="primary"):
        st.session_state.page = "search"
        st.rerun()

def show_popular_movies():
    """Menampilkan film-film populer sebagai quick access"""
    st.subheader("🎭 Film Populer")
    
    popular_queries = ["Avengers", "Spider Man", "Batman", "Avatar", "Iron Man"]
    
    cols = st.columns(5)
    for idx, movie in enumerate(popular_queries):
        with cols[idx]:
            if st.button(f"🎬 {movie}", use_container_width=True):
                st.session_state.page = "search"
                st.session_state["last_query"] = movie
                st.rerun()

def show_import_export():
    """Menampilkan fitur Import/Export"""
    st.subheader("📁 Import & Export Data")
    
    col_import, col_export = st.columns(2)
    
    with col_import:
        st.markdown("### 📥 Import Data")
        uploaded_file = st.file_uploader(
            "Unggah file JSON/CSV", 
            type=['json', 'csv'],
            help="Unggah file hasil export sebelumnya"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.type == "application/json":
                    imported_data = json.load(uploaded_file)
                    st.session_state.imported_data = imported_data
                    st.success(f"✅ Berhasil import {len(imported_data)} film dari JSON!")
                    
                    if st.button("📋 Lihat Data Import"):
                        st.session_state.page = "import_view"
                        st.rerun()
                        
                elif uploaded_file.type == "text/csv":
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    imported_data = []
                    csv_reader = csv.DictReader(stringio)
                    for row in csv_reader:
                        imported_data.append(row)
                    
                    st.session_state.imported_data = imported_data
                    st.success(f"✅ Berhasil import {len(imported_data)} film dari CSV!")
                    
                    if st.button("📋 Lihat Data Import", key="view_csv_import"):
                        st.session_state.page = "import_view"
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error importing file: {str(e)}")
    
    with col_export:
        st.markdown("### 📤 Export Data")
        st.info("Fitur export tersedia di halaman pencarian setelah hasil muncul.")
        
        st.download_button(
            label="📄 Download Template CSV",
            data="title,year,runtime,jwRating,tomatometer\nAvengers,2012,143,0.95,92\n",
            file_name="template_film.csv",
            mime="text/csv"
        )

def show_import_view():
    """Menampilkan data yang diimport"""
    st.title("📋 Data Film yang Diimport")
    
    if st.button("← Kembali"):
        st.session_state.page = "start"
        st.rerun()
    
    imported_data = st.session_state.get("imported_data", [])
    
    if not imported_data:
        st.warning("Tidak ada data yang diimport")
        return
    
    st.success(f"🎉 Berhasil mengimport {len(imported_data)} film!")
    
    for i, item in enumerate(imported_data):
        with st.container(border=True):
            col1, col2 = st.columns([1, 4])
            with col1:
                poster = item.get("poster") or item.get("poster_url")
                if poster:
                    try:
                        st.image(poster, use_container_width=True)
                    except:
                         st.info("No Image")
                else:
                    st.info("No Image")
            with col2:
                st.subheader(item.get("title", "Tanpa Judul"))
                st.write(item.get("overview", ""))

# === LOGIKA UTAMA DETAIL DAN REKOMENDASI ===
def show_movie_detail():
    """
    Halaman ini muncul SETELAH user menekan tombol 'Lihat Detail & Rekomendasi'.
    Di sini kita menampilkan detail film yang dipilih + Rekomendasi AI.
    """
    movie = st.session_state.selected_movie
    if not movie:
        st.warning("Tidak ada film yang dipilih. Kembali ke pencarian.")
        st.session_state.page = "search"
        st.rerun()
        return

    # Tombol kembali ke hasil pencarian
    if st.button("← Kembali ke Hasil Pencarian"):
        st.session_state.page = "search"
        st.rerun()
        
    st.markdown("---")
    
    # --- BAGIAN 1: DETAIL MOVIE YANG DIPILIH ---
    st.title(movie.get("title", "Detail Film"))
    
    col_poster, col_info = st.columns([1, 3])
    
    with col_poster:
        poster = movie.get("poster")
        if poster:
            try:
                st.image(poster, use_container_width=True)
            except:
                st.image("https://via.placeholder.com/400x600/f0f0f0/808080?text=Poster+Tidak+Tersedia", use_container_width=True)
        else:
            st.image("https://via.placeholder.com/400x600/f0f0f0/808080?text=Poster+Tidak+Tersedia", use_container_width=True)
    
    with col_info:
        st.subheader(f"{movie.get('title', 'Nama Film')} ({movie.get('year', 'Tahun tidak diketahui')})")
        
        # Mendapatkan data awal
        overview_from_api = movie.get("overview")
        current_title = movie.get("title")

        # --- LOGIKA PENANGANAN DESKRIPSI (TETAP MENGGUNAKAN GEMINI JIKA API GAGAL) ---
        if overview_from_api:
            # Jika API eksternal sukses memberikan deskripsi
            st.markdown(f"**Ringkasan (dari API):** {overview_from_api[:250]}...")
        else:
            # Jika API eksternal GAGAL, panggil Gemini untuk membuat deskripsi
            cache_key = f"description_cache_{current_title}"
            
            # Cek cache atau generate baru
            if cache_key not in st.session_state or st.session_state[cache_key] is None:
                with st.spinner(f"Ringkasan tidak tersedia. AI sedang membuat deskripsi untuk '{current_title}'..."):
                    ai_description = get_movie_description(current_title)
                    st.session_state[cache_key] = ai_description
            
            final_description = st.session_state[cache_key]
            
            if final_description:
                st.markdown(f"**Ringkasan (dibuat AI):** {final_description}")
            else:
                st.markdown("**Ringkasan:** *Tidak ada deskripsi singkat tersedia.*")
        # --- AKHIR LOGIKA DESKRIPSI ---
            
        st.markdown("---")

        # Rating & Runtime
        # MENGHILANGKAN SEMUA LOGIKA PEMANGGILAN GEMINI UNTUK IMDb RATING.
        # HANYA MENGGUNAKAN JUSTWATCH DAN ROTTENTOMATOES DARI API EKSTERNAL.
        imdb_rating_val = None # Pastikan ini None agar tidak mengganggu

        # Data rating dari API eksternal yang lama
        jwRating = movie.get("jwRating")
        tomatometer = movie.get("tomatometer")
        runtime = movie.get("runtime")

        cols_metric = st.columns(3)

        # Gunakan JustWatch Rating
        if jwRating:
            jwRating_percent = math.ceil(jwRating * 100)
            unlike = 100 - jwRating_percent
            pieChartData = pd.DataFrame({"values":["Like", "Dislike"], "category": [jwRating_percent, unlike]})
            fig = px.pie(pieChartData, values="category", names="values", hole=0.5)

            with cols_metric[0]:
                st.metric("⭐ JustWatch", f"{jwRating_percent}%")
                st.plotly_chart(fig)
        else:
             with cols_metric[0]:
                st.info("JustWatch Rating tidak tersedia.")
            

        if tomatometer:
            with cols_metric[1]:
                st.metric("🍅 RottenTomatoes", f"{tomatometer}%")
        if runtime:
            with cols_metric[2]:
                st.metric("⏱ Durasi", f"{runtime} min")
                
        link = movie.get("link")
        if link:
            st.markdown(f"[🔗 Lihat detail lengkap di JustWatch]({link})")
            
    # --- BAGIAN 2: REKOMENDASI AI (TETAP MENGGUNAKAN GEMINI) ---
    st.markdown("---")
    st.header(f"🤖 Karena kamu melihat '{movie.get('title')}'")
    st.caption("Berikut adalah rekomendasi film serupa berdasarkan analisis AI (IMDb Data):")

    # Kita gunakan judul film yang sedang dilihat sebagai query ke Gemini
    # Caching untuk Rekomendasi
    if "recommendations_cache" not in st.session_state or st.session_state.get("current_rec_movie") != current_title:
        with st.spinner(f"Sedang mencari film yang mirip dengan '{current_title}'..."):
            rec_results = get_movie_recommendations(current_title)
            st.session_state.recommendations_cache = rec_results
            st.session_state.current_rec_movie = current_title
    
    recommendations = st.session_state.recommendations_cache

    if isinstance(recommendations, dict) and "error" in recommendations:
        st.error(recommendations["error"])
    elif isinstance(recommendations, list) and recommendations:
        # Tampilkan dalam Grid 3 Kolom
        cols_per_row = 3
        rows = [recommendations[i:i + cols_per_row] for i in range(0, len(recommendations), cols_per_row)]

        for row in rows:
            cols = st.columns(cols_per_row)
            for idx, rec in enumerate(row):
                with cols[idx]:
                    with st.container(border=True):
                        # Gambar Poster Rekomendasi
                        img_url = rec.get("image_url")
                        if img_url and img_url.startswith("http"):
                            try:
                                st.image(img_url, use_container_width=True)
                            except:
                                st.image("https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg", use_container_width=True)
                        else:
                             st.image("https://via.placeholder.com/300x450?text=No+Image", use_container_width=True)
                        
                        st.markdown(f"**{rec.get('judul_film')}**")
                        st.caption(f"⭐ IMDb: {rec.get('imdb_rating')}")
    else:
        st.info("Tidak ada rekomendasi yang ditemukan.")

    st.markdown("---")

def show_search_page():
    
    @st.cache_data(ttl=300)
    def fetch_movies(query: str, timeout=8):
        """Ambil data film dari API"""
        if not query: return []
        q = quote_plus(query)
        url = f"https://imdb.iamidiotareyoutoo.com/justwatch?q={q}" 
        try:
            resp = requests.get(url, timeout=timeout)
            data = resp.json()
            # Parsing data API yang kadang formatnya beda-beda
            results = []
            if isinstance(data, list): results = data
            elif isinstance(data, dict):
                if "description" in data and isinstance(data["description"], list): results = data["description"]
                elif "data" in data: results = data["data"]
                else: results = [data] # Fallback
            
            # Normalisasi Data
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                # Ambil poster dari berbagai kemungkinan key
                poster = item.get("poster") or item.get("poster_url") or item.get("photo_url")
                if isinstance(poster, list) and poster: poster = poster[0]
                if not poster: poster = ""
                
                normalized.append({
                    "title": item.get("title", "No Title"),
                    "year": item.get("year", ""),
                    "runtime": item.get("runtime", ""),
                    "jwRating": item.get("jwRating", ""),
                    "tomatometer": item.get("tomatometer", ""),
                    "poster": poster,
                    "overview": item.get("overview") or item.get("short_description") or "",
                    "link": item.get("url", "")
                })
            return normalized

        except Exception as e:
            return {"_error": str(e)}

    # Tombol kembali
    if st.button("← Kembali ke Beranda"):
        st.session_state.page = "start"
        st.rerun()
    
    st.title("🔍 Pencarian Film")
    st.markdown("---")

    # HISTORY PENCARIAN
    if st.session_state.search_history:
        with st.expander("📚 History Pencarian Terakhir"):
            hist_cols = st.columns(3)
            for idx, hist in enumerate(reversed(st.session_state.search_history[-3:])):
                if idx < 3:
                    with hist_cols[idx]:
                        if st.button(f"🔍 {hist}", use_container_width=True, key=f"hist_btn_{idx}"):
                            st.session_state["last_query"] = hist
                            st.rerun()

    col1, col2 = st.columns([3,1])
    with col1:
        initial_value = st.session_state.get("last_query", "")
        search_query = st.text_input("Nama film", value=initial_value, placeholder="Misal: Avatar, Avengers")
    with col2:
        st.write("") # Spacer layout
        st.write("")
        search_button = st.button("Cari Film", type="primary", use_container_width=True)

    # Logika Pencarian
    if search_button or (search_query and search_query != st.session_state.get("last_executed_query")):
        st.session_state["last_executed_query"] = search_query # Tandai query ini sudah dijalankan
        st.session_state["last_query"] = search_query
        
        # Simpan History
        if search_query not in st.session_state.search_history:
            st.session_state.search_history.append(search_query)

        with st.spinner("Mencari film..."):
            results = fetch_movies(search_query)
        
        st.session_state.search_results = results # Simpan hasil

    # Tampilkan Hasil
    results = st.session_state.search_results
    
    if isinstance(results, dict) and "_error" in results:
        st.error(f"Error: {results['_error']}")
    elif isinstance(results, list) and results:
        st.success(f"Ditemukan {len(results)} film.")
        
        # === FITUR EXPORT (JSON/CSV) ===
        with st.expander("📤 Export Hasil Pencarian"):
            col_json, col_csv = st.columns(2)
            # JSON Export
            json_str = json.dumps(results, indent=2)
            col_json.download_button("Download JSON", data=json_str, file_name=f"hasil_{search_query}.json", mime="application/json")
            
            # CSV Export
            csv_buffer = StringIO()
            if results:
                writer = csv.DictWriter(csv_buffer, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
                col_csv.download_button("Download CSV", data=csv_buffer.getvalue(), file_name=f"hasil_{search_query}.csv", mime="text/csv")

        # === TAMPILAN GRID FILM ===
        cards_per_row = 3
        for i in range(0, len(results), cards_per_row):
            row = results[i:i+cards_per_row]
            cols = st.columns(cards_per_row)

            for idx, item in enumerate(row):
                with cols[idx]:
                    with st.container(border=True):
                        # Poster
                        poster = item.get("poster")
                        if poster:
                            try:
                                st.image(poster, use_container_width=True)
                            except:
                                st.image("https://via.placeholder.com/300x450?text=No+Image", use_container_width=True)
                        
                        st.subheader(f"{item.get('title')}")
                        st.caption(f"Tahun: {item.get('year')}")
                        
                        # LOGIKA TOMBOL DETAIL (SESUAI REQUEST)
                        # Ketika tombol ini ditekan, kita simpan data film dan pindah halaman
                        btn_key = f"detail_{i}{idx}{item.get('title')}"
                        if st.button("Lihat Detail & Rekomendasi", key=btn_key, use_container_width=True, type="primary"):
                            st.session_state.selected_movie = item
                            st.session_state.page = "detail"
                            st.rerun()

# =================ROUTING UTAMA=================
if st.session_state.page == "start":
    show_start_page()
elif st.session_state.page == "import_view":
    show_import_view()
elif st.session_state.page == "detail":
    show_movie_detail()
else:
    show_search_page()
