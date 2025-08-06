import streamlit as st
import pandas as pd
import requests
from io import StringIO

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

st.title("📺 YouTube Trending (API)")
st.markdown("Consulta videos populares por país usando la API oficial de YouTube.")

country_name = st.selectbox("Selecciona un país:", list(COUNTRIES.keys()))
country_code = COUNTRIES[country_name]
max_results = st.slider("Número de videos a mostrar:", min_value=5, max_value=50, value=20, step=5)

if st.button("🔍 Obtener tendencias"):
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={country_code}&maxResults={max_results}&key={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        videos = []
        for item in data.get("items", []):
            video = {
                "Título": item["snippet"]["title"],
                "Canal": item["snippet"]["channelTitle"],
                "Vistas": int(item["statistics"].get("viewCount", 0)),
                "Enlace": f"https://www.youtube.com/watch?v={item['id']}"
            }
            videos.append(video)

        df = pd.DataFrame(videos)
        st.success(f"{len(df)} videos extraídos para {country_name}.")
        st.dataframe(df)

        csv = StringIO()
        df.to_csv(csv, index=False)
        st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name=f"trending_{country_code}.csv", mime="text/csv")

    else:
        st.error(f"Error al consultar la API: {response.status_code}")


