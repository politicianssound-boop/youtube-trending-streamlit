import streamlit as st
import pandas as pd
import requests
import re
import datetime
from collections import Counter
import matplotlib.pyplot as plt

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis Avanzado")

tabs = st.tabs(["🔥 Trending", "🔍 Buscar", "🧠 Explorar Canal", "🌱 Nicho"])

COUNTRIES = {"México": "MX", "España": "ES", "Estados Unidos": "US", "India": "IN", "Brasil": "BR", "Canadá": "CA"}

def parse_iso8601_duration(duration: str) -> str:
    pattern = r"^P(?:\d+D)?T(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?$"
    m = re.match(pattern, duration)
    if not m:
        return duration
    parts = {k: int(v) if v else 0 for k, v in m.groupdict().items()}
    total = parts["h"] * 3600 + parts["m"] * 60 + parts["s"]
    hrs, rem = divmod(total, 3600)
    mins, secs = divmod(rem, 60)
    return f"{hrs:d}:{mins:02d}:{secs:02d}" if hrs else f"{mins:d}:{secs:02d}"

# 🔥 Trending
with tabs[0]:
    st.markdown("Videos en tendencia por país, categoría y palabra clave.")
    country = st.selectbox("País (tendencias):", list(COUNTRIES.keys()))
    maxr = st.slider("Max videos:", 5, 50, 20)
    kw = st.text_input("Filtrar título (opcional):")

    cat_data = requests.get(
        f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={COUNTRIES[country]}&key={API_KEY}"
    ).json()
    categories = {"Todas": None}
    for c in cat_data.get("items", []):
        categories[c["snippet"]["title"]] = c["id"]
    cat_sel = st.selectbox("Categoría (opcional):", list(categories.keys()))

    if st.button("Obtener tendencias"):
        url = (
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails"
            f"&chart=mostPopular&regionCode={COUNTRIES[country]}&maxResults={maxr}&key={API_KEY}"
        )
        resp = requests.get(url).json()
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        rows = []
        for it in resp.get("items", []):
            title = it["snippet"]["title"]
            cid = it["snippet"]["categoryId"]
            cat_name = next((k for k, v in categories.items() if v == cid), "Desconocida")
            if (not kw or kw.lower() in title.lower()) and (categories[cat_sel] is None or categories[cat_sel] == cid):
                rows.append({
                    "Título": title,
                    "Canal": it["snippet"]["channelTitle"],
                    "Vistas": int(it["statistics"].get("viewCount", 0)),
                    "Likes": int(it["statistics"].get("likeCount", 0)),
                    "Duración": parse_iso8601_duration(it["contentDetails"]["duration"]),
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

# 🔍 Buscar
with tabs[1]:
    st.markdown("Buscar global o por país, con visitas, likes, duración.")
    query = st.text_input("Palabra clave:")
    country_opt = st.selectbox("País (opcional):", [""] + list(COUNTRIES.keys()))
    maxr2 = st.slider("Max resultados:", 5, 50, 20)
    order_opt = st.selectbox("Ordenar por:", ["relevance", "date", "viewCount", "rating", "title"])

    if st.button("Buscar"):
        url = (
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults={maxr2}"
            f"&q={query}&order={order_opt}&key={API_KEY}"
        )
        if country_opt:
            url += f"&regionCode={COUNTRIES[country_opt]}"
        sr = requests.get(url).json()
        ids = [i["id"]["videoId"] for i in sr.get("items", [])]
        stats = {}
        if ids:
            stats = {
                v["id"]: v for v in requests.get(
                    f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(ids)}"
                ).json().get("items", [])
            }

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
        if not df2.empty:
            st.dataframe(df2)
            st.download_button("Descargar CSV", df2.to_csv(index=False), "search.csv", "text/csv")
        else:
            st.warning("Sin resultados.")

# 🧠 Explorar Canal
# 🧠 Explorar Canal
with tabs[2]:
    st.markdown("Explorar canal por ID. Se muestran perfil completo, videos y estadísticas.")
    cid = st.text_input("Channel ID:")
    order_opt = st.selectbox("Ordenar videos por:", ["Publicado", "Vistas", "Likes", "Título"])
    videos_per_page = st.slider("Videos por página:", 10, 50, 20)

    if st.button("Explorar"):
        ch = requests.get(
            f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics,contentDetails&id={cid}&key={API_KEY}"
        ).json()

        if ch.get("items"):
            c0 = ch["items"][0]

            st.image(c0["snippet"]["thumbnails"]["default"]["url"], width=100)
            st.subheader(c0["snippet"]["title"])
            st.markdown(f"""
                **Suscriptores:** {c0['statistics'].get('subscriberCount','N/A')}  
                **Total vistas:** {c0['statistics'].get('viewCount','N/A')}  
                **Videos:** {c0['statistics'].get('videoCount','N/A')}  
                **Descripción:** {c0['snippet']['description']}
            """)

            # Obtener todos los videos de la playlist de subidas
            pl = c0["contentDetails"]["relatedPlaylists"]["uploads"]
            all_videos = []
            next_page = None

            while True:
                vids_url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={pl}&maxResults=50&key={API_KEY}"
                if next_page:
                    vids_url += f"&pageToken={next_page}"

                vids_req = requests.get(vids_url).json()
                all_videos.extend(vids_req.get("items", []))
                next_page = vids_req.get("nextPageToken")

                if not next_page:
                    break

            ids = [i["contentDetails"]["videoId"] for i in all_videos]
            stats = {}
            for i in range(0, len(ids), 50):  # la API permite máx. 50 IDs por consulta
                batch_ids = ids[i:i+50]
                stats.update({
                    v["id"]: v for v in requests.get(
                        f"https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&key={API_KEY}&id={','.join(batch_ids)}"
                    ).json().get("items", [])
                })

            rows, dates, durations = [], [], []
            for it in all_videos:
                vid = it["contentDetails"]["videoId"]
                stt = stats.get(vid, {})
                pub = it["snippet"]["publishedAt"][:10]
                dates.append(datetime.datetime.fromisoformat(pub))
                dur_raw = stt.get("contentDetails", {}).get("duration", "PT0S")
                dur_fmt = parse_iso8601_duration(dur_raw)
                dur_secs = sum(int(x) * 60**i for i, x in enumerate(reversed(dur_fmt.split(":"))))
                durations.append(dur_secs)
                rows.append({
                    "Título": it["snippet"]["title"],
                    "Publicado": pub,
                    "Vistas": int(stt.get("statistics", {}).get("viewCount", 0)),
                    "Likes": int(stt.get("statistics", {}).get("likeCount", 0)),
                    "Duración": dur_fmt,
                    "Enlace": f"https://youtu.be/{vid}"
                })

            df3 = pd.DataFrame(rows)
            orden_mapping = {
                "Publicado": "Publicado",
                "Vistas": "Vistas",
                "Likes": "Likes",
                "Título": "Título"
            }
            orden_col = orden_mapping.get(order_opt, "Publicado")
            df3 = df3.sort_values(orden_col, ascending=False).reset_index(drop=True)

            # Paginación
            total_pages = (len(df3) - 1) // videos_per_page + 1
            page = st.number_input("Página:", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * videos_per_page
            end_idx = start_idx + videos_per_page
            st.dataframe(df3.iloc[start_idx:end_idx])

            # Métricas
            if len(dates) > 1:
                frec = (max(dates) - min(dates)) / (len(dates) - 1)
                st.write("📅 Frecuencia entre publicaciones:", frec)

            if durations:
                avg_sec = sum(durations) / len(durations)
                avg_dur = datetime.timedelta(seconds=int(avg_sec))
                st.write("⏱️ Duración promedio:", avg_dur)

            # Gráfico
            plt.figure(figsize=(6, 4))
            plt.barh(df3["Título"].head(20), df3["Vistas"].head(20))
            plt.gca().invert_yaxis()
            st.pyplot(plt)

            st.download_button("⬇️ Descargar CSV", df3.to_csv(index=False), "channel_videos.csv", "text/csv")
        else:
            st.error("Channel ID inválido.")


# 🌱 Nicho
with tabs[3]:
    st.markdown("Análisis básico de nicho: palabras frecuentes en títulos (canal activo).")
    if 'df3' in locals():
        words = " ".join(df3["Título"].tolist()).lower().split()
        common = Counter([w.strip(".,!?") for w in words if len(w) > 3]).most_common(20)
        df_niche = pd.DataFrame(common, columns=["Palabra", "Frecuencia"])
        st.bar_chart(df_niche.set_index("Palabra"))
    else:
        st.info("Primero explora un canal para analizar sus títulos aquí.")

