import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

API_KEY = st.secrets["YOUTUBE_API_KEY"]

st.title("📺 YouTube Análisis y Descubrimiento")

tabs = st.tabs(["🔥 Videos en tendencia", "🔍 Buscar por palabra clave", "🧠 Explorar canal"])

# Lista de países y su código
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

# TAB 1 – TRENDING
with tabs[0]:
    st.markdown("Consulta videos en **tendencia actual** por país, categoría y palabra clave (en el título).")

    country_name = st.selectbox("🌍 País:", list(COUNTRIES.keys()))
    country_code = COUNTRIES[country_name]
    max_results = st.slider("🎥 Número de videos:", 5, 50, 20)
    keyword = st.text_input("🔍 Filtrar por palabra en el título (opcional):")

    # Obtener categorías disponibles
    cat_url = f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={country_code}&key={API_KEY}"
    cat_data = requests.get(cat_url).json()
    categories = {"Todas": None}
    for cat in cat_data.get("items", []):
        categories[cat["snippet"]["title"]] = cat["id"]

    category_filter = st.selectbox("🎯 Filtrar por categoría (opcional):", list(categories.keys()))

    if st.button("Obtener tendencias"):
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={country_code}&maxResults={max_results}&key={API_KEY}"
        res = requests.get(url)
        data = res.json()
        today = datetime.now().strftime("%Y-%m-%d")

        videos = []
        for item in data.get("items", []):
            cat_id = item["snippet"]["categoryId"]
            cat_name = next((k for k, v in categories.items() if v == cat_id), "Desconocida")
            title = item["snippet"]["title"]

            # Filtrar por keyword y categoría si es necesario
            if (not keyword or keyword.lower() in title.lower()) and (
                categories[category_filter] is None or categories[category_filter] == cat_id
            ):
                videos.append({
                    "Título": title,
                    "Canal": item["snippet"]["channelTitle"],
                    "Vistas": int(item["statistics"].get("viewCount", 0)),
                    "Likes": int(item["statistics"].get("likeCount", 0)),
                    "Fecha publicación": item["snippet"]["publishedAt"][:10],
                    "Categoría": cat_name,
                    "Trending date": today,
                    "Enlace": f"https://www.youtube.com/watch?v={item['id']}",
                    "Channel ID": item["snippet"]["channelId"]
                })

        if videos:
            df = pd.DataFrame(videos)
            st.success(f"{len(df)} videos encontrados.")
            st.dataframe(df)
            csv = StringIO()
            df.to_csv(csv, index=False)
            st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name="trending.csv", mime="text/csv")
        else:
            st.warning("No se encontraron videos con esos filtros.")

# TAB 2 – SEARCH
with tabs[1]:
    st.markdown("Busca videos por palabra clave en cualquier país, aunque no estén en tendencia.")

    query = st.text_input("🔑 Palabra clave a buscar (ej. apache)", "")
    region = st.selectbox("🌍 País:", list(COUNTRIES.keys()))
    region_code = COUNTRIES[region]
    qty = st.slider("🎥 Resultados:", 5, 50, 20)

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
                    "Enlace": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    "Channel ID": item["snippet"]["channelId"]
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

# TAB 3 – CANAL
with tabs[2]:
    st.markdown("🎯 Ingresa el **ID del canal** que puedes obtener desde las pestañas anteriores (columna 'Channel ID').")

    channel_id = st.text_input("🔗 Channel ID:", "")

    if st.button("Explorar canal"):
        if not channel_id:
            st.warning("Debes ingresar un Channel ID.")
        else:
            ch_url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={channel_id}&key={API_KEY}"
            ch_res = requests.get(ch_url).json()

            if "items" in ch_res and len(ch_res["items"]) > 0:
                ch = ch_res["items"][0]
                ch_title = ch["snippet"]["title"]
                ch_desc = ch["snippet"]["description"]
                ch_thumb = ch["snippet"]["thumbnails"]["default"]["url"]
                ch_subs = ch["statistics"].get("subscriberCount", "N/A")
                ch_views = ch["statistics"].get("viewCount", "N/A")
                ch_videos = ch["statistics"].get("videoCount", "N/A")

                st.image(ch_thumb, width=80)
                st.subheader(ch_title)
                st.markdown(f"**Suscriptores:** {ch_subs} | **Vistas totales:** {ch_views} | **Videos:** {ch_videos}")
                st.markdown(f"📄 _{ch_desc}_")

                # Obtener videos más vistos del canal
                search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&order=viewCount&type=video&maxResults=10&key={API_KEY}"
                vids = requests.get(search_url).json()
                top_videos = []
                for item in vids.get("items", []):
                    top_videos.append({
                        "Título": item["snippet"]["title"],
                        "Fecha": item["snippet"]["publishedAt"][:10],
                        "Enlace": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    })

                if top_videos:
                    df_top = pd.DataFrame(top_videos)
                    st.markdown("📈 **Videos más vistos del canal:**")
                    st.dataframe(df_top)

                    csv = StringIO()
                    df_top.to_csv(csv, index=False)
                    st.download_button("⬇️ Descargar CSV", data=csv.getvalue(), file_name="canal_videos.csv", mime="text/csv")
                else:
                    st.info("Este canal no tiene videos públicos disponibles.")
            else:
                st.error("No se encontró el canal. Verifica el ID.")

