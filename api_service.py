# api_service.py
# Service untuk handle API calls

import requests
from urllib.parse import quote_plus

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

    return normalize_movie_data(results)

def normalize_movie_data(raw_results):
    """Normalisasi data film dari API"""
    normalized = []
    
    for item in raw_results:
        if not isinstance(item, dict):
            normalized.append({"raw": item})
            continue

        # Ambil data sesuai struktur dari file yang diberikan
        title = item.get("title") or ""
        year = item.get("year") or ""
        runtime = item.get("runtime") or ""
        jwRating = item.get("jwRating") or ""
        tomatometer = item.get("tomatometer") or ""
        tomatocertifiedFresh = item.get("tomatocertifiedFresh") or False
        offers = item.get("offers") or []

        # Handle poster URL
        poster = get_poster_url(item)
        
        # Overview/deskripsi
        overview = (
            item.get("overview")
            or item.get("short_description")
            or item.get("description")
            or item.get("plot")
            or ""
        )

        # Link
        link = item.get("url") or ""

        normalized.append({
            "title": title,
            "year": year,
            "runtime": runtime,
            "jwRating": jwRating,
            "tomatometer": tomatometer,
            "tomatocertifiedFresh": tomatocertifiedFresh,
            "offers": offers,
            "poster": poster,
            "overview": overview,
            "link": link,
            "raw": item,
        })

    return normalized

def get_poster_url(item):
    """Extract poster URL dari berbagai field yang mungkin"""
    poster = (
        item.get("poster")
        or item.get("poster_url")
        or item.get("photo_url")
        or item.get("thumbnail")
        or item.get("image")
        or item.get("poster_path")
        or ""
    )

    # Poster jika list → ambil elemen pertama
    if isinstance(poster, list) and len(poster) > 0:
        poster = poster[0]

    # Fix URL tanpa https
    if isinstance(poster, str) and poster.startswith("//"):
        poster = "https:" + poster

    # Jika bukan string → kosongkan
    if not isinstance(poster, str):
        poster = ""

    return poster