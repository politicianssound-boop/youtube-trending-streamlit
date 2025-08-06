import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

# Lista de países compatibles con YouTube API
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

API_KEY = st.secrets["YOUTUBE_API_KEY"]

st.title("📺 YouTube Trending (API Extendida)")
st.markdown("Consulta videos populares por país y filtra por palabra clave.")

country_name = st.selectbox("Selecciona un país:", list(COUNTRIES.keys()))
country_code = COUNTRIES[country_name]
max_results = st.slider("Número de videos a mostrar:", min_value=5, max_value=50, value=20, step=5)
keyword = st.text_input("🔍 Filtrar por palabra clave (opcional)", "")

if st.button("🔍 Obtener tendencias"):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={country_code}&maxResults={max_results}&key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # Obtener categorías para mapear
        cat_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={country_code}&key={API_KEY}"
        cat_resp = requests.get(cat_url)
        category_map = {}
        if cat_resp.status_code == 200:
            for cat in cat_resp.json().get("items", []):
                category_map[cat["id"]] = cat["snippet"]["title"]

        videos = []
        today = datetime.now().strftime("%Y-%m-%d")

        for item in data.get("items", []):
            title = item["snippet"]["title"]
            if keyword.lower() in title.lower():
                video = {
                    "Título": title,
                    "Canal": item["snippet"]["channelTitle"],
                    "Vistas": int(item["statistics"].get("viewCount", 0)),
                    "Likes": int(item["statistics"].get("likeCount", 0)),
                    "Fecha publicación": item["snippet"]["publishedAt"][:10],
                    "Categoría": category_map.get(item["snippet"]["categoryId"], "Desconocida"),
                    "Trending date": today,
                    "Enlace": f"https://www.youtube.com/watch?v={item['id']}"
                }
                videos.append(video)

        if videos:
            df = pd.DataFrame(videos)
            st.success(f"{len(df)} videos encontrados para {country_name}.")
            st.dataframe(df)

            csv = StringIO()
            df.to_csv(csv, index=False)
            st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name=f"trending_{country_code}_{today}.csv", mime="text/csv")
        else:
            st.warning("No se encontraron videos con esa palabra clave.")
    else:
        st.error(f"Error al consultar la API: {response.status_code}")




