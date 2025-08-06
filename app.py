import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import pandas as pd
from io import StringIO

# Lista de países disponibles en YouTube Trending
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

st.title("📺 Scraper de YouTube Trending")
st.markdown("Extrae videos en tendencia por país directamente desde YouTube.")

# Parámetros del usuario
country_name = st.selectbox("Selecciona un país:", list(COUNTRIES.keys()))
country_code = COUNTRIES[country_name]

max_videos = st.slider("Número de videos a extraer:", min_value=5, max_value=50, value=20, step=5)

if st.button("🔍 Obtener tendencias"):
    st.info(f"Extrayendo top {max_videos} videos de {country_name}...")

    # Configurar Selenium en modo headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    url = f"https://www.youtube.com/feed/trending?gl={country_code}"
    driver.get(url)
    time.sleep(5)

    titles = []
    channels = []
    links = []

    video_elements = driver.find_elements(By.TAG_NAME, "ytd-video-renderer")
    for i, video in enumerate(video_elements[:max_videos]):
        try:
            title_elem = video.find_element(By.ID, "video-title")
            titles.append(title_elem.text)
            links.append(title_elem.get_attribute("href"))

            channel_elem = video.find_element(By.XPATH, ".//*[@id='channel-info']//yt-formatted-string")
            channels.append(channel_elem.text)
        except:
            continue

    driver.quit()

    df = pd.DataFrame({
        "Título": titles,
        "Canal": channels,
        "Enlace": links
    })

    st.success(f"{len(df)} videos extraídos.")
    st.dataframe(df)

    # Botón para descargar
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Descargar CSV",
        data=csv_buffer.getvalue(),
        file_name=f"trending_{country_code}.csv",
        mime="text/csv"
    )
