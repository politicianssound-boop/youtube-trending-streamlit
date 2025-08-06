# TAB 3 – EXPLORAR CANAL
with tabs[2]:
    st.markdown("🔍 Ingresa el **ID de un canal** para explorar su contenido.")
    channel_id = st.text_input("🔗 ID del canal (ej. UC_x5XG1OV2P6uZZ5FSM9Ttw)", "")

    if st.button("Explorar canal"):
        if not channel_id:
            st.warning("Debes ingresar un Channel ID válido.")
        else:
            # Obtener info del canal
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

                # Obtener videos recientes con más vistas
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

