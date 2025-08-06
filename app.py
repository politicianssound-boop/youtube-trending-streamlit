import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

API_KEY = st.secrets["YOUTUBE_API_KEY"]

st.title("📺 YouTube Análisis y Búsqueda")

tabs = st.tabs(["🔥 Videos en tendencia", "🔍 Buscar por palabra clave"])

# TAB 1 – TRENDING
with tabs[0]:
    COUNTRIES = {
        "Argentina": "AR",
        "Brasil": "BR",
        "Canadá": "CA",
        "Chile": "CL",
        "Colombia": "CO",
        "Francia": "FR",
        "Alemania": "DE",
        "India": "IN",
        "Italia": "IT",
        "Japón": "JP",
        "México": "MX",
        "Países Bajos": "NL",
        "Rusia": "RU",
        "España": "ES",
        "Reino Unido": "GB",
        "Estados Unidos": "US",
        "Corea del Sur": "KR"
    }

    country_name = st.selectbox("Selecciona un país:", list(COUNTRIES.keys()))
    country_code = COUNTRIES[country_name]
    max_results = st.slider("Número de videos a mostrar:", min_value=5, max_value=50, value=20, step=5)
    keyword = st.text_input("🔍 Filtrar en título (opcional)", "")

    if st.button("Obtener tendencias"):
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={country_code}&maxResults={max_results}&key={API_KEY}"
        res = requests.get(url)
        data = res.json()

        # Obtener categorías
        cat_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={country_code}&key={API_KEY}"
        cat_data = requests.get(cat_url).json()
        category_map = {cat["id"]: cat["snippet"]["title"] for cat in cat_data.get("items", [])}

        videos = []
        today = datetime.now().strftime("%Y-%m-%d")

        for item in data.get("items", []):
            title = item["snippet"]["title"]
            if keyword.lower() in title.lower():
                videos.append({
                    "Título": title,
                    "Canal": item["snippet"]["channelTitle"],
                    "Vistas": int(item["statistics"].get("viewCount", 0)),
                    "Likes": int(item["statistics"].get("likeCount", 0)),
                    "Fecha publicación": item["snippet"]["publishedAt"][:10],
                    "Categoría": category_map.get(item["snippet"]["categoryId"], "Desconocida"),
                    "Trending date": today,
                    "Enlace": f"https://www.youtube.com/watch?v={item['id']}"
                })

        if videos:
            df = pd.DataFrame(videos)
            st.success(f"{len(df)} videos encontrados.")
            st.dataframe(df)
            csv = StringIO()
            df.to_csv(csv, index=False)
            st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name="trending.csv", mime="text/csv")
        else:
            st.warning("No se encontraron videos con ese filtro.")

# TAB 2 – KEYWORD SEARCH
with tabs[1]:
    st.markdown("Busca videos por palabra clave usando la API de YouTube.")
    query = st.text_input("🔑 Escribe una palabra clave para buscar (ej. apache)", "")
    region = st.selectbox("País para resultados:", list(COUNTRIES.keys()))
    region_code = COUNTRIES[region]
    qty = st.slider("Número de resultados", 5, 50, 20)

    if st.button("Buscar"):
        search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&regionCode={region_code}&maxResults={qty}&key={API_KEY}"
        search_res = requests.get(search_url)

        if search_res.status_code == 200:
            search_data = search_res.json()
            results = []
            for item in search_data.get("items", []):
                results.append({
                    "Título": item["snippet"]["title"],
                    "Canal": item["snippet"]["channelTitle"],
                    "Fecha publicación": item["snippet"]["publishedAt"][:10],
                    "Enlace": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                })

            if results:
                df_search = pd.DataFrame(results)
                st.success(f"{len(df_search)} resultados encontrados.")
                st.dataframe(df_search)

                csv = StringIO()
                df_search.to_csv(csv, index=False)
                st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name="busqueda.csv", mime="text/csv")
            else:
                st.warning("No se encontraron videos para esa búsqueda.")
        else:
            st.error(f"Error al consultar la API: {search_res.status_code}")
