import streamlit as st
import pandas as pd
import requests
import re
import datetime
from collections import Counter
import matplotlib.pyplot as plt

API_KEY = st.secrets["YOUTUBE_API_KEY"]
st.title("📺 YouTube Análisis Avanzado")

# Lista de pestañas
tabs_labels = ["Tendencias", "Buscar", "Explorar Canal", "Nicho", "Ideas de Nicho", "Popularidad"]

# Recuperar pestaña activa desde session_state o por defecto la primera
active_tab_label = st.session_state.get("active_tab", tabs_labels[0])
active_tab_index = tabs_labels.index(active_tab_label)

# Crear pestañas
tabs = st.tabs(tabs_labels)

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
# (Se mantiene igual que en tu código actual)

# 🌱 Nicho mejorado
with tabs[3]:
    st.markdown("Analiza canales pequeños para encontrar oportunidades de nicho.")

    default_kw = st.session_state.get("nicho_kw", "")
    kw_niche = st.text_input("Palabra clave o categoría:", value=default_kw)
    max_subs = st.number_input("Máx. suscriptores:", min_value=0, value=50000)
    max_views = st.number_input("Máx. vistas totales:", min_value=0, value=5000000)
    months_old = st.slider("Máx. antigüedad de vídeos (meses):", 1, 6, 2)
    max_results_niche = st.slider("Máx. vídeos a analizar:", 10, 200, 100)
    
    faceless_keywords = ["compilation", "animation", "gameplay", "tutorial", "music", "sound", "relax", "asmr", "lofi"]

    if st.button("Buscar nichos") or (default_kw and st.session_state.get("auto_search", False)):
        st.session_state["auto_search"] = False
        if not kw_niche:
            st.warning("Introduce una palabra clave para iniciar la búsqueda.")
        else:
            fecha_limite = (datetime.datetime.utcnow() - datetime.timedelta(days=30*months_old)).isoformat("T") + "Z"
            base_url = (
                f"https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&order=viewCount"
                f"&q={kw_niche}&publishedAfter={fecha_limite}&key={API_KEY}"
            )

            all_videos = []
            next_page = None
            while len(all_videos) < max_results_niche:
                url = base_url + "&maxResults=50"
                if next_page:
                    url += f"&pageToken={next_page}"
                res = requests.get(url).json()
                all_videos.extend(res.get("items", []))
                next_page = res.get("nextPageToken")
                if not next_page:
                    break

            canales_unicos = {}
            niche_words = []
            for item in all_videos:
                ch_id = item["snippet"]["channelId"]
                if ch_id in canales_unicos:
                    continue
                ch_data = requests.get(
                    f"https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&id={ch_id}&key={API_KEY}"
                ).json()
                if ch_data.get("items"):
                    c0 = ch_data["items"][0]
                    subs = int(c0["statistics"].get("subscriberCount", 0))
                    views_total = int(c0["statistics"].get("viewCount", 0))
                    if subs <= max_subs and views_total <= max_views:
                        title = c0["snippet"]["title"]
                        desc = c0["snippet"]["description"]
                        is_faceless = any(word in (title.lower() + desc.lower()) for word in faceless_keywords)
                        ratio = views_total / subs if subs > 0 else 0
                        canales_unicos[ch_id] = {
                            "Canal": title,
                            "Suscriptores": subs,
                            "Vistas totales": views_total,
                            "Ratio vistas/suscriptor": round(ratio, 2),
                            "Faceless probable": "Sí" if is_faceless else "No",
                            "Enlace": f"https://www.youtube.com/channel/{ch_id}"
                        }
                niche_words.extend(item["snippet"]["title"].lower().split())

            st.subheader(f"Resultados: {len(canales_unicos)} canales encontrados")
            if canales_unicos:
                df_channels = pd.DataFrame(canales_unicos.values()).sort_values("Suscriptores")
                st.dataframe(df_channels)
                st.download_button("⬇️ Descargar CSV", df_channels.to_csv(index=False), "nicho_canales.csv", "text/csv")
                common_words = Counter([w.strip(".,!?") for w in niche_words if len(w) > 3]).most_common(15)
                df_words = pd.DataFrame(common_words, columns=["Palabra", "Frecuencia"])
                st.subheader("Palabras clave más usadas en títulos")
                st.bar_chart(df_words.set_index("Palabra"))
            else:
                st.info("No se encontraron canales que cumplan con los filtros.")

# 🧭 Ideas de Nicho
with tabs[4]:
    st.markdown("Genera ideas de nichos a partir de tendencias en YouTube sin introducir palabras clave.")
    country_ideas = st.selectbox("🌍 País:", list(COUNTRIES.keys()))
    max_videos_ideas = st.slider("Max vídeos a analizar:", 10, 50, 30)

    if st.button("Generar ideas"):
        url = (
            f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics"
            f"&chart=mostPopular&regionCode={COUNTRIES[country_ideas]}&maxResults={max_videos_ideas}&key={API_KEY}"
        )
        res = requests.get(url).json()
        palabras, categorias = [], []
        for item in res.get("items", []):
            title_words = item["snippet"]["title"].lower().split()
            palabras.extend([w.strip(".,!?") for w in title_words if len(w) > 3])
            categorias.append(item["snippet"]["categoryId"])
        top_palabras = Counter(palabras).most_common(20)
        st.subheader("Palabras más frecuentes en títulos de tendencias")
        for palabra, freq in top_palabras:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{palabra} ({freq})")
            with col2:
                if st.button("Analizar", key=f"analizar_{palabra}"):
                    st.session_state["nicho_kw"] = palabra
                    st.session_state["active_tab"] = "Nicho"
                    st.session_state["auto_search"] = True
                    st.experimental_rerun()
        cat_url = (
            f"https://www.googleapis.com/youtube/v3/videoCategories?part=snippet&regionCode={COUNTRIES[country_ideas]}&key={API_KEY}"
        )
        cats_data = requests.get(cat_url).json()
        cat_map = {c["id"]: c["snippet"]["title"] for c in cats_data.get("items", [])}
        cat_count = Counter([cat_map.get(cid, "Desconocida") for cid in categorias])
        df_cats = pd.DataFrame(cat_count.items(), columns=["Categoría", "Frecuencia"])
        st.subheader("Categorías más frecuentes en tendencias")
        st.dataframe(df_cats)

from pytrends.request import TrendReq
import matplotlib.dates as mdates

with tabs[5]:
    st.markdown("Analiza la popularidad de una palabra clave en YouTube según Google Trends.")

    kw_trend = st.text_input("Palabra clave para analizar:")
    timeframes = {
        "Última hora": "now 1-H",
        "Últimas 4 horas": "now 4-H",
        "Último día": "now 1-d",
        "Últimos 7 días": "now 7-d",
        "Últimos 30 días": "today 1-m",
        "Últimos 90 días": "today 3-m",
        "Últimos 12 meses": "today 12-m",
        "Últimos 5 años": "today+5-y",
        "Desde 2008": "all"
    }
    period = st.selectbox("Periodo de análisis:", list(timeframes.keys()))

    if st.button("Analizar tendencia"):
        if not kw_trend:
            st.warning("Introduce una palabra clave.")
        else:
            pytrends = TrendReq(hl='es-ES', tz=0)
            pytrends.build_payload([kw_trend], cat=0, timeframe=timeframes[period], geo="", gprop="youtube")
            df_trend = pytrends.interest_over_time()

            if not df_trend.empty:
                df_trend = df_trend.drop(columns=["isPartial"], errors="ignore")
                st.line_chart(df_trend)

                avg_interest = df_trend[kw_trend].mean()
                last_value = df_trend[kw_trend].iloc[-1]
                st.write(f"📊 **Interés medio:** {avg_interest:.2f}")
                st.write(f"📈 **Último valor:** {last_value}")

                if last_value > avg_interest:
                    st.success("Tendencia al alza 📈")
                elif last_value < avg_interest:
                    st.error("Tendencia a la baja 📉")
                else:
                    st.info("Tendencia estable ➡️")
            else:
                st.warning("No se encontraron datos para esa palabra clave en YouTube.")



