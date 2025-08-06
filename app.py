import streamlit as st
import pandas as pd
import requests
import re
import datetime
from io import StringIO
import matplotlib.pyplot as plt

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis Avanzado")

tabs = st.tabs(["🔥 Trending", "🔍 Buscar", "🧠 Explorar Canal"])

COUNTRIES = {"México": "MX", "España": "ES", "Estados Unidos": "US", "India": "IN", "Brasil": "BR", "Canadá": "CA"}

def parse_iso8601_duration(duration: str) -> str:
    pattern = r"^P(?:\d+D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
    m = re.match(pattern, duration)
    if not m:
        return duration
    parts = {k: int(v) if v else 0 for k, v in m.groupdict().items()}
    td = datetime.timedelta(hours=parts["hours"], minutes=parts["minutes"], seconds=parts["seconds"])
    total = int(td.total_seconds())
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hrs:d}:{mins:02d}:{secs:02d}" if hrs else f"{mins:d}:{secs:02d}"

# TAB 2: Buscar (añadiendo orden y campos)
with tabs[1]:
    st.markdown("Buscar por palabra clave. Opcional país y orden de resultados.")
    query = st.text_input("Palabra clave:")
    country_opt = st.selectbox("País (opcional):", [""] + list(COUNTRIES.keys()))
    maxr = st.slider("Max resultados:", 5, 50, 20)
    order_opt = st.selectbox("Ordenar por:", ["relevance", "date", "viewCount", "rating", "title"])
    if st.button("Buscar"):
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults={maxr}&q={query}&order={order_opt}&key={API_KEY}"
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
                "Duración": parse_iso8601_duration(stt.get("contentDetails", {}).get("duration", "")),
                "Enlace": f"https://youtu.be/{vid}",
                "Channel ID": i["snippet"]["channelId"]
            })
        df2 = pd.DataFrame(rows)
        st.write("Orden:", order_opt)
        st.dataframe(df2)
        st.download_button("Descargar CSV", df2.to_csv(index=False), "search.csv", "text/csv")
# TAB 3: Explorar Canal (frecuencia y duración promedio)
with tabs[2]:
    st.markdown("Explorar canal por ID. Incluye frecuencia y duración promedio.")
    cid = st.text_input("Channel ID:")
    if st.button("Explorar"):
        ch = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}").json()
        if ch.get("items"):
            c0 = ch["items"][0]
            st.subheader(c0["snippet"]["title"])
            st.write(f"Subs: {c0['statistics'].get('subscriberCount','N/A')} | Total vistas: {c0['statistics'].get('viewCount','N/A')}")
            pl = c0["contentDetails"]["relatedPlaylists"]["uploads"]
            vids = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={pl}&maxResults=20&key={API_KEY}").json()
            rows, dates = [], []
            ids = [item["contentDetails"]["videoId"] for item in vids.get("items", [])]
            stats = {v["id"]: v for v in requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(ids)}"
            ).json().get("items", [])}
            for it in vids.get("items", []):
                vid = it["contentDetails"]["videoId"]
                stt = stats.get(vid, {})
                pub = it["snippet"]["publishedAt"][:10]
                dates.append(datetime.datetime.fromisoformat(pub))
                rows.append({
                    "Título": it["snippet"]["title"],
                    "Publicado": pub,
                    "Vistas": int(stt.get("statistics", {}).get("viewCount", 0)),
                    "Likes": int(stt.get("statistics", {}).get("likeCount", 0)),
                    "Duración": parse_iso8601_duration(stt.get("contentDetails", {}).get("duration","")),
                    "Enlace": f"https://youtu.be/{vid}"
                })
            df3 = pd.DataFrame(rows)
            st.dataframe(df3)
            if len(dates) > 1:
                frec = (max(dates) - min(dates)) / (len(dates)-1)
                st.write("Frecuencia aproximada entre videos:", frec)
            # Gráfico de vistas
            plt.figure(figsize=(6,4))
            plt.barh(df3["Título"], df3["Vistas"])
            plt.gca().invert_yaxis()
            st.pyplot(plt)
            st.download_button("Descargar CSV", df3.to_csv(index=False), "channel_videos.csv", "text/csv")
        else:
            st.error("Channel ID inválido.")
