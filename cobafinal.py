import streamlit as st
import requests
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

API_URL = "https://imdb.iamidiotareyoutoo.com/justwatch?q="

# -----------------------------------------------------------
# Function: Search movie
# -----------------------------------------------------------
def search_movie(title):
    try:
        response = requests.get(API_URL + title)
        response.raise_for_status()
        return response.json()
    except:
        return None

# -----------------------------------------------------------
# Function: Build recommendation graph
# -----------------------------------------------------------
def build_graph(movies):
    G = nx.Graph()
    for movie in movies:
        mid = movie.get('id')
        mtitle = movie.get('title')
        genres = movie.get('genre', [])
        if mid and mtitle:
            G.add_node(mid, label=mtitle)
            for g in genres:
                G.add_node(g, label=g)
                G.add_edge(mid, g)
    return G

# -----------------------------------------------------------
# UI Layout
# -----------------------------------------------------------
st.title("🎬 Movie Recommender & Search App")

st.markdown("---")
st.subheader("🔎 Cari Film")

query = st.text_input("Judul film:")

if st.button("Search Movie"):
    if query.strip() == "":
        st.warning("Masukkan judul film terlebih dahulu!")
    else:
        data = search_movie(query)
        if not data or 'results' not in data:
            st.error("Film tidak ditemukan atau API error.")
        else:
            results = data['results']
            if len(results) == 0:
                st.warning("Tidak ada hasil ditemukan.")
            else:
                st.success(f"Ditemukan {len(results)} hasil film.")

                df = pd.DataFrame(results)
                st.dataframe(df)

                st.markdown("---")
                st.subheader("📌 Graph Genre Connections")

                G = build_graph(results)

                plt.figure(figsize=(10, 6))
                pos = nx.spring_layout(G, k=0.5)
                nx.draw(G, pos, with_labels=False, node_size=500)
                labels = nx.get_node_attributes(G, 'label')
                nx.draw_networkx_labels(G, pos, labels, font_size=8)
                st.pyplot(plt)

st.markdown("---")
st.caption("Versi Final — Movie Search & Recommender App")