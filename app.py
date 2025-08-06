import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import matplotlib.pyplot as plt

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis y Descubrimiento")

tabs = st.tabs(["🔥 Trending", "🔍 Buscar", "🧠 Explorar Canal"])

COUNTRIES = {"México": "MX", "España": "ES", "Estados Unidos": "US", "India": "IN", "Brasil": "BR", "Canadá": "CA"}

# — TAB 1: Trending —
with tabs[0]:
    st.markdown("Tendencias por país, categoría y palabra clave.")
    country = st.selectbox("País (tendencias):", list(COUNTRIES.keys()))
    maxr = st.slider("Max videos:", 5, 50, 20)
    kw = st.text_input("Filtrar título (opcional):")

    # Categorías
    cat_data = requests.get(
        f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={COUNTRIES[country]}&key={API_KEY}"
    ).json()
    categories = {"Todas": None}
    for c in cat_data.get("items", []):
        categories[c["snippet"]["title"]] = c["id"]
    cat_sel = st.selectbox("Categoría (opcional):", list(categories.keys()))

    if st.button("Obtener tendencias"):
        url = (f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails"
               f"&chart=mostPopular&regionCode={COUNTRIES[country]}&maxResults={maxr}&key={API_KEY}")
        resp = requests.get(url).json()
        today = datetime.now().strftime("%Y-%m-%d")
        rows = []
        for it in resp.get("items", []):
            title = it["snippet"]["title"]
            cid = it["snippet"]["categoryId"]
            cat_name = next((k for k,v in categories.items() if v==cid), "Desconocida")
            if (not kw or kw.lower() in title.lower()) and (categories[cat_sel] is None or categories[cat_sel]==cid):
                rows.append({
                    "Título": title,
                    "Canal": it["snippet"]["channelTitle"],
                    "Vistas": int(it["statistics"].get("viewCount", 0)),
                    "Likes": int(it["statistics"].get("likeCount", 0)),
                    "Duración": it["contentDetails"]["duration"],
                    "Categoría": cat_name,
                    "Publicado": it["snippet"]["publishedAt"][:10],
                    "Fecha": today,
                    "Enlace": f"https://youtu.be/{it['id']}",
                    "Channel ID": it["snippet"]["channelId"]
                })
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df)
            st.download_button("Descargar CSV", df.to_csv(index=False), "trending.csv", "text/csv")
        else:
            st.warning("No hay videos con esos filtros.")

# — TAB 2: Search —
with tabs[1]:
    st.markdown("Buscar global o por país, con visitas, likes, duración.")
    query = st.text_input("Palabra clave:")
    country_opt = st.selectbox("País (opcional):", [""] + list(COUNTRIES.keys()))
    maxr2 = st.slider("Max resultados:", 5, 50, 20)
    order_opt = st.selectbox("Ordenar por:", ["relevance", "date", "viewCount", "rating", "title"])
    if st.button("Buscar"):
        url = (f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults={maxr2}"
               f"&q={query}&order={order_opt}&key={API_KEY}")
        if country_opt:
            url += f"&regionCode={COUNTRIES[country_opt]}"
        sr = requests.get(url).json()
        ids = [i["id"]["videoId"] for i in sr.get("items", [])]
        stats = {}
        if ids:
            stats = {v["id"]: v for v in requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(ids)}"
            ).json().get("items", [])}
        rows = []
        for i in sr.get("items", []):
            vid = i["id"]["videoId"]
            stt = stats.get(vid, {})
            rows.append({
                "Título": i["snippet"]["title"],
                "Canal": i["snippet"]["channelTitle"],
                "Publicado": i["snippet"]["publishedAt"][:10],
                "Vistas": int(stt.get("statistics", {}).get("viewCount", 0)),
                "Likes": int(stt.get("statistics", {}).get("likeCount", 0)),
                "Duración": stt.get("contentDetails", {}).get("duration", ""),
                "Enlace": f"https://youtu.be/{vid}",
                "Channel ID": i["snippet"]["channelId"]
            })
        df2 = pd.DataFrame(rows)
        if not df2.empty:
            st.dataframe(df2)
            st.download_button("Descargar CSV", df2.to_csv(index=False), "search.csv", "text/csv")
        else:
            st.warning("Sin resultados.")

# — TAB 3: Explorar Canal —
with tabs[2]:
    st.markdown("Explora un canal por ID (cópialo de las otras pestañas).")
    cid = st.text_input("Channel ID:")
    if st.button("Explorar"):
        ch = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}").json()
        if ch.get("items"):
            c0 = ch["items"][0]
            st.image(c0["snippet"]["thumbnails"]["default"]["url"])
            st.subheader(c0["snippet"]["title"])
            st.write(f"Subs: {c0['statistics'].get('subscriberCount','N/A')} | Total vistas: {c0['statistics'].get('viewCount','N/A')}")
            playlist = c0["contentDetails"]["relatedPlaylists"]["uploads"]
            vids = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={playlist}&maxResults=10&key={API_KEY}").json()
            rows = []
            ids = [item["contentDetails"]["videoId"] for item in vids.get("items", [])]
            stats = {v["id"]: v for v in requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(ids)}"
            ).json().get("items", [])}
            for it in vids.get("items", []):
                vid = it["contentDetails"]["videoId"]
                stt = stats.get(vid, {})
                rows.append({
                    "Título": it["snippet"]["title"],
                    "Publicado": it["snippet"]["publishedAt"][:10],
                    "Vistas": int(stt.get("statistics", {}).get("viewCount", 0)),
                    "Likes": int(stt.get("statistics", {}).get("likeCount", 0)),
                    "Duración": stt.get("contentDetails", {}).get("duration",""),
                    "Enlace": f"https://youtu.be/{vid}"
                })
            df3 = pd.DataFrame(rows)
            st.dataframe(df3)
            # Gráfico de vistas reales
            plt.figure(figsize=(6, 4))
            plt.barh(df3["Título"], df3["Vistas"])
            plt.gca().invert_yaxis()
            st.pyplot(plt)
            st.download_button("Descargar CSV", df3.to_csv(index=False), "channel_videos.csv", "text/csv")
        else:
            st.error("Channel ID inválido.")
