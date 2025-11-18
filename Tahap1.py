import streamlit as st
import requests
from urllib.parse import quote_plus

st.set_page_config(page_title="Cari Film (API IMDb/JustWatch)", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "start"

if "genre" not in st.session_state:
    st.session_state.genre = None

if "rating" not in st.session_state:
    st.session_state.rating = None


@st.cache_data(ttl=300)
def fetch_movies(query: str, timeout=8):
    """Ambil data film dari API"""
    if not query:
        return []

    q = quote_plus(query)
    url = f"https://imdb.iamidiotareyoutoo.com/justwatch?q={q}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StreamlitApp/1.0)",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"_error": str(e)}

    results = []
    if isinstance(data, dict):
        for key in ("items", "results", "data", "searchResults"):
            if key in data and isinstance(data[key], list):
                results = data[key]
                break
        if not results:
            if "title" in data:
                results = [data]
            else:
                for v in data.values():
                    if isinstance(v, list):
                        results = v
                        break
    elif isinstance(data, list):
        results = data

    normalized = []
    for item in results:
        if not isinstance(item, dict):
            normalized.append({"raw": item})
            continue

        title = item.get("title") or item.get("name") or item.get("original_title") or ""

        year = (
            item.get("original_release_year")
            or item.get("year")
            or item.get("release_year")
            or item.get("release_date", "")
        )
        if isinstance(year, str) and len(year) >= 4:
            year = year[:4]

        poster = (
            item.get("poster")
            or item.get("poster_url")
            or item.get("photo_url")
            or item.get("thumbnail")
            or item.get("image")
            or item.get("poster_path")
            or ""
        )

        if isinstance(poster, list) and poster:
            poster = poster[0]
        if isinstance(poster, str) and poster.startswith("//"):
            poster = "https:" + poster
        if not isinstance(poster, str):
            poster = ""

        overview = (
            item.get("overview")
            or item.get("short_description")
            or item.get("description")
            or item.get("plot")
            or ""
        )

        link = (
            item.get("url")
            or item.get("imdb_url")
            or item.get("original_url")
            or item.get("jw_url")
            or ""
        )

        normalized.append(
            {
                "title": title,
                "year": year,
                "poster": poster,
                "overview": overview,
                "link": link,
                "raw": item,
            }
        )

    return normalized


if st.session_state.page == "start":
    st.title(" Selamat Datang di Movie Recomender")
    st.markdown("Mulai pilih preferensi dulu sebelum mencari film!")

    genre = st.selectbox(
        "Pilih Genre",
        ["Action", "Drama", "Comedy", "Horror", "Romance", "Sci-Fi", "Thriller", "Animation"],
    )

    rating = st.slider("Minimal Rating IMDb", 1, 10, 7)

    start_btn = st.button(" Mulai Cari Film")

    if start_btn:
        st.session_state.genre = genre
        st.session_state.rating = rating
        st.session_state.page = "search"
        st.rerun()

    st.stop()



back = st.button(" Kembali ke Halaman Awal")
if back:
    st.session_state.page = "start"
    st.rerun()

st.title(" Pencarian Film — IMDb / JustWatch API")
st.markdown(
    f"Genre pilihan: **{st.session_state.genre}**, Minimum Rating: **{st.session_state.rating}** ⭐"
)

st.markdown("---")
st.subheader(" Cari Film Favoritmu")

col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Nama film", value="", placeholder="Misal: Avatar, Avengers, Dilan")
with col2:
    search_button = st.button("Cari Film")

if search_button or (search_query and st.session_state.get("last_query") != search_query and search_query.strip() != ""):
    st.session_state["last_query"] = search_query

    if search_query.strip() == "":
        st.warning("Isi dulu nama filmnya ya...")
    else:
        with st.spinner("Lagii cariin nih..."):
            results = fetch_movies(search_query.strip())

        if isinstance(results, dict) and results.get("_error"):
            st.error(f"Error: {results['_error']}")
        elif not results:
            st.info("Film tidak ditemukan, coba judul lain.")
        else:
            st.markdown(f"**Hasil untuk:** `{search_query}` — **{len(results)}** film ditemukan")

            cards_per_row = 3
            for i in range(0, len(results), cards_per_row):
                row = results[i:i + cards_per_row]
                cols = st.columns(cards_per_row)

                for c, item in zip(cols, row):
                    with c:
                        title = item.get("title") or "—"
                        year = item.get("year") or ""
                        overview = item.get("overview") or ""
                        poster = item.get("poster") or ""
                        link = item.get("link") or ""

                        if poster:
                            try:
                                st.image(poster, use_container_width=True)
                            except:
                                st.write("(gambar error)")

                        st.markdown(f"**{title}** {f'({year})' if year else ''}")

                        if overview:
                            st.caption(overview if len(overview) < 200 else overview[:197] + "...")

                        if link:
                            if link.startswith("/"):
                                possible = "https://www.imdb.com" + link
                            else:
                                possible = link
                            st.markdown(f"[📖 Lihat detail]({possible})")

                        with st.expander("Lihat data lengkap"):
                            raw = item.get("raw")
                            clean_raw = dict(raw) if isinstance(raw, dict) else raw

                            hidden_fields = [
                                "photo_url",
                                "backdrops",
                                "poster",
                                "poster_url",
                                "poster_path",
                                "thumbnail",
                                "image",
                            ]

                            if isinstance(clean_raw, dict):
                                for f in hidden_fields:
                                    if f in clean_raw:
                                        del clean_raw[f]

                            st.json(clean_raw)

st.markdown("---")
st.caption("WELL WELL WELL")

