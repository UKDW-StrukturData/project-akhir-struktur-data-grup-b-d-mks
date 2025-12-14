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

GEMINI_API_KEY = "AIzaSyBTpIRX_QHvCPgb6pQQOOvns10JYR-Av-0" 

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
if "selected_comparison_movies" not in st.session_state:
    st.session_state.selected_comparison_movies = []


# =================HELPER FUNGSI BARU=================

def get_average_runtime(movie_list):
    """Menghitung durasi rata-rata dari semua film yang ada (hasil cari + import)."""
    runtimes = []
    # Gabungkan data untuk menghindari duplikasi saat menghitung rata-rata
    unique_movies = {}
    for movie in movie_list:
        title = movie.get("title")
        if title and title not in unique_movies:
            unique_movies[title] = movie

    for movie in unique_movies.values():
        try:
            # Pastikan runtime adalah string dan bisa diubah ke float
            runtime_str = movie.get("runtime")
            if runtime_str:
                runtime_val = float(runtime_str)
                if runtime_val > 0:
                    runtimes.append(runtime_val)
        except (ValueError, TypeError):
            continue
    
    if not runtimes:
        return 0
    return sum(runtimes) / len(runtimes)


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
    # Menggunakan GEMINI_API_KEY dari kode yang diberikan
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
    # Menggunakan GEMINI_API_KEY dari kode yang diberikan
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
                        # Normalisasi keys untuk konsistensi dengan hasil pencarian
                        normalized_row = {
                             "title": row.get("title", row.get("judul")),
                             "year": row.get("year", row.get("tahun")),
                             "runtime": row.get("runtime", row.get("durasi")),
                             "jwRating": row.get("jwRating"),
                             "tomatometer": row.get("tomatometer"),
                             "overview": row.get("overview") or row.get("deskripsi"),
                             "poster": row.get("poster_url") or row.get("poster"),
                        }
                        imported_data.append(normalized_row)
                    
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
            data="title,year,runtime,jwRating,tomatometer,overview,poster\nAvengers,2012,143,0.95,92,Sekelompok pahlawan super berkumpul,null,null\n",
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
    
    st.success(f"Berhasil mengimport {len(imported_data)} film!")
    
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

# === LOGIKA UTAMA DETAIL DAN REKOMENDASI DENGAN GRAFIK BATANG ===
def show_movie_detail():
    """
    Halaman ini muncul SETELAH user menekan tombol 'Lihat Detail & Rekomendasi'.
    Di sini kita menampilkan detail film yang dipilih + Rekomendasi AI + Grafik Perbandingan.
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
            cache_key = f"description_cache_{current_title}"
            
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
        jwRating = movie.get("jwRating")
        tomatometer = movie.get("tomatometer")
        runtime = movie.get("runtime")

        # --- STRUKTUR 3 KOLOM: [JustWatch + Pie] | [Rotten Tomatoes] | [Durasi + Bar Chart] ---
        cols_metric = st.columns(3) 

        # Gunakan JustWatch Rating (Kolom 1)
        if jwRating:
            try:
                # JustWatch rating (0-1) dikalikan 100
                jwRating_percent = math.ceil(float(jwRating) * 100) 
                unlike = 100 - jwRating_percent
                pieChartData = pd.DataFrame({"values":["Like", "Dislike"], "category": [jwRating_percent, unlike]})
                fig = px.pie(pieChartData, values="category", names="values", hole=0.5, color_discrete_sequence=['#4CAF50', '#FF5722'])

                with cols_metric[0]:
                    st.metric("JustWatch", f"{jwRating_percent}%")
                    st.plotly_chart(fig, use_container_width=True)
            except ValueError:
                with cols_metric[0]:
                    st.info("JustWatch Rating tidak valid.")
        else:
              with cols_metric[0]:
                st.info("JustWatch Rating tidak tersedia.")
            
        # Rotten Tomatoes (Kolom 2)
        if tomatometer:
            try:
                tomatometer_val = float(tomatometer)
                with cols_metric[1]:
                    st.metric("RottenTomatoes", f"{tomatometer_val}%")
            except ValueError:
                pass 
        
        # Durasi Film Terpilih & Grafik Perbandingan Durasi (Kolom 3)
        current_runtime_val = 0
        with cols_metric[2]:
            if runtime:
                try:
                    current_runtime_val = float(runtime)
                    # Metrik Durasi Film Ini
                    st.metric("⏱ Durasi Film Ini", f"{current_runtime_val} min")
                except ValueError:
                    pass
            
            # Subheader untuk Grafik Durasi Perbandingan
            # st.subheader("Vs Rata-rata") # Dihilangkan karena title grafik sudah cukup
            
            # Dapatkan semua film yang tersedia (hasil pencarian + import)
            available_movies = (
                st.session_state.search_results + 
                st.session_state.imported_data
            )
            average_runtime = get_average_runtime(available_movies)

            if current_runtime_val > 0 and average_runtime > 0:
                # Siapkan data untuk grafik perbandingan
                durasi_data = pd.DataFrame({
                    "Kategori": ["Film Ini", "Rata-rata"],
                    "Durasi": [current_runtime_val, average_runtime]
                })

                # Buat bar chart menggunakan Plotly Express
                fig_durasi_comp = px.bar(
                    durasi_data,
                    x="Kategori",
                    y="Durasi",
                    color="Kategori",
                    color_discrete_map={
                        "Film Ini": "#2196F3", # Biru
                        "Rata-rata": "#FFC107" # Kuning
                    },
                    text_auto=True,
                    title="Durasi (menit)"
                )
                fig_durasi_comp.update_layout(
                    showlegend=False, 
                    margin=dict(t=50, b=0, l=0, r=0), # Kurangi margin atas
                    height=250 # Atur tinggi agar lebih ringkas
                ) 
                fig_durasi_comp.update_traces(marker_line_width=0)
                st.plotly_chart(fig_durasi_comp, use_container_width=True)
            else:
                st.info("Data durasi atau rata-rata tidak tersedia.")
                
        #Menampilkan Link Streaming dari Film Yang Dipilih
        title = movie.get("title") or movie.get("originalTitle") or ""
        year = movie.get("year") or ""
        st.header(f"{title} ({year})")

        def get_streaming_links_from_imdb(judul):
            try:
                q = requests.utils.quote(judul)
                url = f"https://imdb.iamidiotareyoutoo.com/justwatch?q={q}"

                resp = requests.get(url, timeout=10).json()
                if not resp.get("ok"):
                    return []

                des = resp.get("description", [])
                if len(des) == 0:
                    return []

                # ambil film pertama yang paling relevan
                return des[0].get("offers", [])

            except Exception:
                return []
            
        judul_film = title
        streaming_offers = get_streaming_links_from_imdb(judul_film)

        st.markdown("---")
        st.subheader("Tempat Menonton Film Ini")

        if not streaming_offers:
            st.info("Tidak ada data streaming yang tersedia dari API IMDB.")
        else:
            unique = {}
            for item in streaming_offers:
                url = item.get("url")
                if url and url not in unique:
                    unique[url] = item

            for item in unique.values():
                nama = item.get("name", "-")
                tipe = item.get("type", "-").replace("_", "")
                link = item.get("url", "#")
                with st.container():
                    st.markdown(
                        f"""
                        <div style="
                            padding: 15px;
                            border-radius: 12px;
                            background: #cccccc;
                            border: 1px solid #333;
                            margin-bottom: 10px;
                        ">
                            <h3 style="margin: 0; color: white;">{nama}</h3>
                            <p style="margin: 0; color: #cccccc;">📌 {tipe}</p>
                            <a href="{link}" target="_blank" style="
                                display: inline-block;
                                margin-top: 8px;
                                padding: 8px 12px;
                                background: #11111;
                                border-radius: 8px;
                                color: black;
                                font-weight: bold;
                                text-decoration: none;
                            ">🔗 Tonton di sini</a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            
    # --- BAGIAN 2: REKOMENDASI AI ---
    st.markdown("---")
    st.header(f"Karena kamu melihat '{movie.get('title')}'")
    st.caption("Berikut adalah rekomendasi film serupa berdasarkan analisis AI (IMDb Data):")

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
    
    # --- BAGIAN 3: GRAFIK PERBANDINGAN RATING DAN DURASI (BAR CHART) ---
    
    st.header("Perbandingan Film dari Rating & Durasi")
    st.caption("Bandingkan film ini dengan film lain dari hasil pencarian/import.")
    
    # Gabungkan semua data film yang tersedia untuk perbandingan
    available_movies_for_comparison = (
        st.session_state.search_results + 
        st.session_state.imported_data
    )
    
    # Tambahkan film yang sedang dilihat (jika belum ada)
    current_movie_title = movie.get("title")
    if not any(m.get("title") == current_movie_title for m in available_movies_for_comparison):
        available_movies_for_comparison.append(movie) 

    # Hilangkan duplikat berdasarkan judul dan film tanpa judul
    unique_movies_map = {}
    for m in available_movies_for_comparison:
        title = m.get("title")
        if title and title not in unique_movies_map:
            unique_movies_map[title] = m
    
    comparison_data_list = list(unique_movies_map.values())
    
    # Buat dictionary untuk mapping agar mudah diakses
    movie_dict = {m.get("title"): m for m in comparison_data_list}
    movie_titles = list(movie_dict.keys())

    # Filter film yang sedang dilihat dari opsi multiselect
    options_for_select = [title for title in movie_titles if title != current_movie_title]
        
    # Set default pilihan film yang sudah pernah dipilih
    default_selection = [current_movie_title] 

    # Multiselect untuk memilih 3 film
    selected_titles = st.multiselect(
        "Pilih film lain untuk perbandingan (maksimal 3 film tambahan)",
        options=options_for_select,
        default=st.session_state.selected_comparison_movies,
        max_selections=3,
        key="comparison_selector"
    )

    # Gabungkan film yang sedang dilihat dengan film yang dipilih
    final_comparison_titles = default_selection + selected_titles

    if not final_comparison_titles:
        st.info("Pilih film lain untuk melihat perbandingan.")
        return

    # Update session state
    st.session_state.selected_comparison_movies = selected_titles
    
    # Siapkan DataFrame untuk Plotly
    data_for_df = []
    skipped_titles = [] 
    
    for title in final_comparison_titles:
        m = movie_dict.get(title)
        if m:
            # Durasi
            runtime_val = 0
            try:
                runtime_val = float(m.get("runtime") or 0)
            except (ValueError, TypeError):
                runtime_val = 0
            
            # Rating (Prioritas JustWatch, lalu RottenTomatoes)
            rating_val = 0
            try:
                # JW Rating (0-1) * 100
                rating_val = float(m.get("jwRating") or 0) * 100
            except (ValueError, TypeError):
                pass
            
            if rating_val == 0:
                 try:
                     # Tomatometer (%)
                     rating_val = float(m.get("tomatometer") or 0)
                 except (ValueError, TypeError):
                     rating_val = 0

            
            if runtime_val > 0 or rating_val > 0:
                 data_for_df.append({
                     "Film": title,
                     "Durasi (menit)": runtime_val,
                     "Rating (%)": rating_val,
                   })
            else:
                skipped_titles.append(title)


    if skipped_titles:
        st.warning(f"⚠️ Film berikut dilewati dari grafik karena data rating dan durasi tidak tersedia (0): **{', '.join(skipped_titles)}**")

    if not data_for_df:
        st.error("Data perbandingan tidak valid atau semua film yang dipilih tidak memiliki data rating/durasi.")
        return
        
    df = pd.DataFrame(data_for_df)
    
    # IMPLEMENTASI BAR CHART DENGAN 2 KOLOM
    
    col_durasi, col_rating = st.columns(2)
    
    # Grafik Batang untuk Durasi
    with col_durasi:
        st.subheader("⏱ Perbandingan Durasi Film")
        fig_durasi = px.bar(
            df, 
            x="Film", 
            y="Durasi (menit)",
            color="Film", 
            title="Durasi (menit)"
        )
        fig_durasi.update_layout(showlegend=False) 
        st.plotly_chart(fig_durasi, use_container_width=True)

    # Grafik Batang untuk Rating
    with col_rating:
        st.subheader("⭐ Perbandingan Rating Film")
        fig_rating = px.bar(
            df, 
            x="Film", 
            y="Rating (%)", 
            color="Film", 
            title="Rating (%) (JustWatch/RottenTomatoes)",
            range_y=[0, 100] 
        )
        fig_rating.update_layout(showlegend=False)
        st.plotly_chart(fig_rating, use_container_width=True)
    
    st.markdown("---")


def show_search_page():
    
    @st.cache_data(ttl=300)
    def fetch_movies(query: str, timeout=8):
        """Ambil data film dari API"""
        if not query: return []
        q = quote_plus(query)
        # Menggunakan API Key yang sudah dimodifikasi
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
            col_json.download_button("Download JSON", data=json_str, file_name=f"hasil_{st.session_state.get('last_query', 'pencarian')}.json", mime="application/json")
            
            # CSV Export
            csv_buffer = StringIO()
            if results:
                # Ambil semua keys unik dari semua hasil sebagai fieldnames
                all_keys = set()
                for item in results:
                    all_keys.update(item.keys())
                
                writer = csv.DictWriter(csv_buffer, fieldnames=list(all_keys))
                writer.writeheader()
                writer.writerows(results)
                col_csv.download_button("Download CSV", data=csv_buffer.getvalue(), file_name=f"hasil_{st.session_state.get('last_query', 'pencarian')}.csv", mime="text/csv")

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
                        
                        # LOGIKA TOMBOL DETAIL
                        btn_key = f"detail_{i}{idx}{item.get('title')}"
                        if st.button("Lihat Detail & Rekomendasi", key=btn_key, use_container_width=True, type="primary"):
                            st.session_state.selected_movie = item
                            # Reset pilihan perbandingan saat memilih film baru
                            st.session_state.selected_comparison_movies = [] 
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
