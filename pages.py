# pages.py
# Definisi berbagai halaman aplikasi

import streamlit as st
from components import show_popular_movies, show_import_export, show_search_history, show_movie_card, show_export_section, show_import_section
from api_service import fetch_movies
from export_service import export_to_json, export_to_csv, generate_filename

def show_start_page():
    """Halaman awal aplikasi"""
    st.title("🎬 Movie Recommender")
    st.markdown("Cari info film lengkap dengan sekali klik!")
    
    # Tampilkan film populer
    show_popular_movies()
    
    # Fitur Import/Export di halaman awal
    # show_import_export()
    
    st.markdown("---")
    
    st.subheader("Cara Menggunakan:")
    st.markdown("""
    1. **Klik tombol 'Mulai Cari Film'** di bawah
    2. **Masukkan nama film** yang ingin dicari
    3. **Lihat hasil** dengan info lengkap dan poster
    4. **Simpan/Export** hasil pencarian
    5. **Import** data film yang sudah disimpan
    """)
    
    st.markdown("---")
    
    if st.button("🚀 Mulai Cari Film", type="primary"):
        st.session_state.page = "search"
        st.rerun()

def show_import_view():
    """Menampilkan data yang diimport"""
    st.title("📋 Data Film yang Diimport")
    a, b = st.columns([1,1])

    with a:
        show_import_section()

    with b:
        show_export_section()
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("← Kembali"):
            st.session_state.page = "start"
            st.rerun()
    
    imported_data = st.session_state.get("imported_data", [])
    
    if not imported_data:
        st.warning("Tidak ada data yang diimport")
        return
    
    st.success(f"🎉 Berhasil mengimport {len(imported_data)} film!")
    
    # Tampilkan data yang diimport
    for i, item in enumerate(imported_data):
        with st.container():
            st.markdown("---")
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                poster = item.get("poster") or item.get("poster_url") or ""
                if poster:
                    try:
                        st.image(poster, use_container_width=True)
                    except:
                        st.info("📸 Poster tidak tersedia")
                else:
                    st.info("📸 Poster tidak tersedia")
            
            with col2:
                title = item.get("title") or "Judul tidak tersedia"
                year = item.get("year") or ""
                runtime = item.get("runtime") or ""
                jwRating = item.get("jwRating") or ""
                tomatometer = item.get("tomatometer") or ""
                
                st.header(f"{title} {f'({year})' if year else ''}")
                
                # Metrics
                col_metrics = st.columns(4)
                
                if jwRating:
                    with col_metrics[0]:
                        if isinstance(jwRating, (int, float)):
                            st.metric("⭐ JW Rating", f"{jwRating:.1%}")
                
                if tomatometer:
                    with col_metrics[1]:
                        st.metric("🍅 Tomatometer", f"{tomatometer}%")
                
                if runtime:
                    with col_metrics[2]:
                        if isinstance(runtime, int):
                            st.metric("⏱️ Durasi", f"{runtime} min")
                
                # Overview
                overview = item.get("overview") or item.get("description") or ""
                if overview:
                    st.write(overview)
                
                # Link
                link = item.get("link") or item.get("url") or ""
                if link:
                    st.markdown(f"🔗 [Lihat detail]({link})")

def show_search_page():
    """Halaman Movie Recommender"""
    # Tombol kembali
    col_back, col_export = st.columns([1, 5])
    with col_back:
        if st.button("← Kembali ke Beranda"):
            st.session_state.page = "start"
            st.rerun()
    
    st.title("🎬 Movie Recommender")
    st.markdown("Cari info film lengkap dengan sekali klik!")

    # Filter dan sorting
    show_filters()
    
    # History pencarian
    show_search_history()
    
    # Form pencarian
    show_search_form()
    
    st.markdown("---")
    st.caption("WELL WELL WELL - Cari Film Lebih Mudah!")

# def show_filters():
#     """Menampilkan filter dan sorting"""
#     st.markdown("---")
    
#     col_filter1, col_filter2, col_filter3 = st.columns(3)
#     with col_filter1:
#         tahun_min = st.number_input("Tahun Minimal", min_value=1900, max_value=2024, value=1990)
#     with col_filter2:
#         tahun_max = st.number_input("Tahun Maksimal", min_value=1900, max_value=2024, value=2024)
#     with col_filter3:
#         sort_by = st.selectbox(
#             "Urutkan Berdasarkan:",
#             ["Relevansi", "Tahun (Terbaru)", "Tahun (Terlama)", "Rating Tertinggi"]
#         )
    
#     return tahun_min, tahun_max, sort_by

def show_search_form():
    """Form pencarian film"""
    st.subheader("🔍 Cari Film Favoritmu")

    col1, col2 = st.columns([3,1])
    with col1:
        search_query = st.text_input("Nama film", value=st.session_state.get("last_query", ""), 
                                   placeholder="Misal: Avatar, Avengers, Dilan")
    with col2:
        search_button = st.button("Cari Film")

    if search_button or (search_query and st.session_state.get("last_query") != search_query and search_query.strip() != ""):
        handle_search(search_query)

def handle_search(search_query):
    """Handle proses pencarian"""
    # Simpan ke history
    if search_query.strip() and search_query not in st.session_state.search_history:
        st.session_state.search_history.append(search_query)
    
    st.session_state.last_query = search_query

    if search_query.strip() == "":
        st.warning("Isi dulu nama filmnya ya...")
    else:
        with st.spinner("Lagii cariin nih..."):
            results = fetch_movies(search_query.strip())

        if isinstance(results, dict) and results.get("_error"):
            st.error(f"Wah, error nih: {results['_error']}")
        elif not results:
            st.info("Ga ketemu filmnya, coba cari yang lain deh.")
        else:
            # Aplikasi filter dan tampilkan hasil
            show_search_results(results, search_query)

def show_search_results(results, search_query):
    """Menampilkan hasil pencarian"""
    # Dapatkan filter values
    tahun_min = st.session_state.get('tahun_min', 1990)
    tahun_max = st.session_state.get('tahun_max', 2024)
    sort_by = st.session_state.get('sort_by', 'Relevansi')
    
    # Filter dan sort results
    filtered_results = filter_and_sort_results(results, tahun_min, tahun_max, sort_by)
    
    # Simpan hasil ke session state untuk export
    st.session_state.search_results = filtered_results
    
    st.markdown(f"**Hasil untuk:** `{search_query}` — **{len(filtered_results)}** film ditemukan")
    
    # Fitur export
    show_export_buttons(filtered_results, search_query)
    
    # Tampilkan hasil dalam grid
    show_results_grid(filtered_results)
    
    st.markdown("---")
    st.success(f"✅ Menampilkan {len(filtered_results)} hasil pencarian")

def filter_and_sort_results(results, tahun_min, tahun_max, sort_by):
    """Filter dan sort hasil pencarian"""
    # Filter tahun
    filtered_results = []
    for item in results:
        year = item.get("year")
        if year and isinstance(year, (int, str)):
            try:
                year_int = int(year) if isinstance(year, str) and year.isdigit() else year
                if isinstance(year_int, int) and tahun_min <= year_int <= tahun_max:
                    filtered_results.append(item)
            except:
                filtered_results.append(item)
        else:
            filtered_results.append(item)
    
    # Sorting
    if sort_by == "Tahun (Terbaru)":
        filtered_results.sort(key=lambda x: x.get("year") or 0, reverse=True)
    elif sort_by == "Tahun (Terlama)":
        filtered_results.sort(key=lambda x: x.get("year") or 9999)
    elif sort_by == "Rating Tertinggi":
        filtered_results.sort(key=lambda x: x.get("jwRating") or 0, reverse=True)
    
    return filtered_results

def show_export_buttons(filtered_results, search_query):
    """Tombol export hasil pencarian"""
    if filtered_results:
        st.subheader("📤 Export Hasil Pencarian")
        
        col_json, col_csv = st.columns(2)
        
        with col_json:
            json_data = export_to_json(filtered_results)
            st.download_button(
                label="💾 Download JSON",
                data=json_data,
                file_name=f"film_{search_query}_{generate_filename('', search_query)}.json",
                mime="application/json"
            )
        
        with col_csv:
            csv_data = export_to_csv(filtered_results)
            st.download_button(
                label="📊 Download CSV",
                data=csv_data,
                file_name=f"film_{search_query}_{generate_filename('', search_query)}.csv",
                mime="text/csv"
            )

def show_results_grid(filtered_results):
    """Menampilkan grid hasil pencarian"""
    cards_per_row = 3
    for i in range(0, len(filtered_results), cards_per_row):
        row = filtered_results[i:i+cards_per_row]
        cols = st.columns(cards_per_row)

        for c, item in zip(cols, row):
            show_movie_card(item, c)
