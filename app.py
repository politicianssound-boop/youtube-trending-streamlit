import streamlit as st
import pandas as pd
import requests, re
import datetime
from io import StringIO
import matplotlib.pyplot as plt
from collections import Counter

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis Avanzado")

tabs = st.tabs(["🔥 Trending", "🔍 Buscar", "🧠 Explorar Canal", "🌱 Nicho"])

COUNTRIES = {"México": "MX", "España": "ES", "Estados Unidos": "US", "India": "IN", "Brasil": "BR", "Canadá": "CA"}

def parse_iso8601_duration(duration: str) -> str:
    pattern = r"^P(?:\d+D)?T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?$"
    m = re.match(pattern, duration)
    if not m: return duration
    parts = {k: int(v) if v else 0 for k,v in m.groupdict().items()}
    total = parts["h"]*3600 + parts["m"]*60 + parts["s"]
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hrs:d}:{mins:02d}:{secs:02d}" if hrs else f"{mins:d}:{secs:02d}"

# (Trending and Search tabs unchanged; assume they already include duration formatting)

# TAB 3 – EXPLORE CHANNEL
with tabs[2]:
    st.markdown("Explorar canal por ID. Se muestran perfil completo, videos y estadísticas.")
    cid = st.text_input("Channel ID:")
    order_opt = st.selectbox("Ordenar videos por:", ["date", "viewCount", "likeCount"])
    if st.button("Explorar"):
        ch = requests.get(f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}").json()
        if ch.get("items"):
            c0 = ch["items"][0]
            st.image(c0["snippet"]["thumbnails"]["default"]["url"], width=100)
            st.subheader(c0["snippet"]["title"])
            st.markdown(f"**Subscribers:** {c0['statistics'].get('subscriberCount','N/A')} • **Total views:** {c0['statistics'].get('viewCount','N/A')} • **Videos:** {c0['statistics'].get('videoCount','N/A')}")
            st.write(f"**Descripción:** {c0['snippet']['description']}")
            pl = c0["contentDetails"]["relatedPlaylists"]["uploads"]
            vids_req = requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={pl}&maxResults=20&key={API_KEY}").json()
            ids = [i["contentDetails"]["videoId"] for i in vids_req.get("items", [])]
            stats = {v["id"]: v for v in requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(ids)}"
            ).json().get("items", [])}
            rows = []
            dates = []
            durations = []
            for it in vids_req.get("items", []):
                vid = it["contentDetails"]["videoId"]
                stt = stats.get(vid, {})
                pub = it["snippet"]["publishedAt"][:10]
                dates.append(datetime.datetime.fromisoformat(pub))
                dur_sec = stats.get(vid, {}).get("contentDetails",{}).get("duration","PT0S")
                dur_fmt = parse_iso8601_duration(dur_sec)
                durations.append(sum(
                    int(x) * 60**i for i,x in enumerate(reversed(dur_fmt.split(":")))
                ))
                rows.append({
                    "Título": it["snippet"]["title"],
                    "Publicado": pub,
                    "Vistas": int(stt.get("statistics", {}).get("viewCount", 0)),
                    "Likes": int(stt.get("statistics", {}).get("likeCount", 0)),
                    "Duración": dur_fmt,
                    "Enlace": f"https://youtu.be/{vid}"
                })
            df3 = pd.DataFrame(rows)
            df3 = df3.sort_values(order_opt, ascending=False).reset_index(drop=True)
            st.dataframe(df3)
            if len(dates) > 1:
                frec = (max(dates)-min(dates))/(len(dates)-1)
                st.write("Frecuencia entre videos:", frec)
            avg_dur = datetime.timedelta(seconds=int(sum(durations)/len(durations))) if durations else None
            st.write("Duración promedio:", avg_dur)
            plt.figure(figsize=(6,4))
            plt.barh(df3["Título"], df3["Vistas"])
            plt.gca().invert_yaxis()
            st.pyplot(plt)
            st.download_button("Descargar CSV", df3.to_csv(index=False), "channel_videos.csv", "text/csv")

# TAB 4 – NICHO
with tabs[3]:
    st.markdown("Análisis básico de nicho: palabras frecuentes en títulos (canal activo).")
    if 'df3' in locals():
        words = " ".join(df3["Título"].tolist()).lower().split()
        common = Counter([w.strip(".,!?") for w in words if len(w)>3]).most_common(20)
        df_niche = pd.DataFrame(common, columns=["Palabra", "Frecuencia"])
        st.bar_chart(df_niche.set_index("Palabra"))
    else:
        st.info("Primero explora un canal para analizar sus títulos aquí.")

