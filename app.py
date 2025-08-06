import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import matplotlib.pyplot as plt

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis y Descubrimiento")

tabs = st.tabs(["🔥 Trending", "🔍 Buscar", "🧠 Explorar Canal"])

COUNTRIES = {
    "México": "MX", "España": "ES", "Estados Unidos": "US",
    "India": "IN", "Brasil": "BR", "Canadá": "CA"
}

# 1. Trending
with tabs[0]:
    st.markdown("Videos en tendencia por país, categoría y palabra clave (título).")
    country = st.selectbox("País (tendencias):", list(COUNTRIES.keys()))
    cat_id = None  # Mantenemos categoría como antes
    maxr = st.slider("Max videos:", 5, 50, 20)
    kw = st.text_input("Filtrar título (opcional):")
    if st.button("Obtener tendencias"):
        trend_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={COUNTRIES[country]}&maxResults={maxr}&key={API_KEY}"
        resp = requests.get(trend_url).json()
        today = datetime.now().strftime("%Y-%m-%d")
        rows = []
        for item in resp.get("items", []):
            title = item["snippet"]["title"]
            if not kw or kw.lower() in title.lower():
                rows.append({
                    "Título": title,
                    "Canal": item["snippet"]["channelTitle"],
                    "Vistas": int(item["statistics"].get("viewCount", 0)),
                    "Likes": int(item["statistics"].get("likeCount", 0)),
                    "Categoría ID": item["snippet"]["categoryId"],
                    "Publicado": item["snippet"]["publishedAt"][:10],
                    "Fecha": today,
                    "Enlace": f"https://youtu.be/{item['id']}",
                    "Channel ID": item["snippet"]["channelId"]
                })
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df)
            st.download_button("Descargar CSV", df.to_csv(index=False), "trending.csv", "text/csv")
        else:
            st.warning("No hay videos con esos filtros.")

# 2. Search
with tabs[1]:
    st.markdown("Buscar por palabra clave. Dejar país vacío para global.")
    query = st.text_input("Palabra clave:")
    country_opt = st.selectbox("País (opcional):", [""] + list(COUNTRIES.keys()))
    maxr2 = st.slider("Max resultados:", 5, 50, 20)
    if st.button("Buscar"):
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults={maxr2}&q={query}&key={API_KEY}"
        if country_opt:
            url += f"&regionCode={COUNTRIES[country_opt]}"
        res = requests.get(url).json()
        ids = [item["id"]["videoId"] for item in res.get("items", [])]
        stats = {}
        if ids:
            stats_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&key={API_KEY}&id={','.join(ids)}"
            stats = {item["id"]: item["statistics"] for item in requests.get(stats_url).json().get("items", [])}

        rows = []
        for item in res.get("items", []):
            vid = item["id"]["videoId"]
            rows.append({
                "Título": item["snippet"]["title"],
                "Canal": item["snippet"]["channelTitle"],
                "Publicado": item["snippet"]["publishedAt"][:10],
                "Vistas": int(stats.get(vid, {}).get("viewCount", 0)),
                "Likes": int(stats.get(vid, {}).get("likeCount", 0)),
                "Enlace": f"https://youtu.be/{vid}",
                "Channel ID": item["snippet"]["channelId"]
            })
        df2 = pd.DataFrame(rows)
        if not df2.empty:
            st.dataframe(df2)
            st.download_button("Descargar CSV", df2.to_csv(index=False), "search.csv", "text/csv")
        else:
            st.warning("No se encontraron resultados.")

# 3. Explorar Canal
with tabs[2]:
    st.markdown("Explora un canal por ID (copiar de Trending o Search).")
    cid = st.text_input("Channel ID:")
    if st.button("Explorar"):
        ch = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}").json()
        if ch.get("items"):
            ch0 = ch["items"][0]
            st.image(ch0["snippet"]["thumbnails"]["default"]["url"])
            st.subheader(ch0["snippet"]["title"])
            st.write(f"Subs: {ch0['statistics'].get('subscriberCount', 'N/A')} | Total vistas: {ch0['statistics'].get('viewCount','N/A')}")
            pl = ch0["contentDetails"]["relatedPlaylists"]["uploads"]
            vids = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={pl}&maxResults=10&key={API_KEY}").json()
            rows = []
            for it in vids.get("items", []):
                vid_id = it["contentDetails"]["videoId"]
                rows.append({
                    "Título": it["snippet"]["title"],
                    "Publicado": it["snippet"]["publishedAt"][:10],
                    "Enlace": f"https://youtu.be/{vid_id}"
                })
            df3 = pd.DataFrame(rows)
            st.dataframe(df3)
            # Gráfico de conteo (solo ranking)
            plt.figure(figsize=(6, 4))
            plt.barh(df3["Título"], range(len(df3), 0, -1))
            plt.gca().invert_yaxis()
            st.pyplot(plt)
            st.download_button("Descargar CSV", df3.to_csv(index=False), "channel_videos.csv", "text/csv")
        else:
            st.error("ID de canal inválido.")
