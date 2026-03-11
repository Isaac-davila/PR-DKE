import streamlit as st
import os
from groq import Groq
from supabase import create_client
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Supabase Verbindung
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="DKE Audio Intelligence", layout="centered")

st.title("🎙️ DKE Audio Agent")
st.info("Transkribiere MP3s und speichere sie direkt in Supabase.")

# 2. Upload Bereich
uploaded_file = st.file_uploader("MP3 Datei auswählen", type=["mp3"])

if uploaded_file is not None:
    st.audio(uploaded_file)

    if st.button("Transkribieren & Speichern"):
        with st.spinner("Whisper KI extrahiert Text..."):
            try:
                # Transkription via Groq
                file_content = uploaded_file.read()
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, file_content),
                    model="whisper-large-v3",
                    response_format="json"
                )

                text_result = transcription.text

                # 3. In Supabase speichern
                # WICHTIG: Die Tabelle muss 'transcriptions' heißen!
                data = supabase.table("Transcriptions").insert({
                    "filename": uploaded_file.name,
                    "content": text_result
                }).execute()

                st.success("✅ Erfolgreich transkribiert und in DB gespeichert!")
                st.text_area("Extrahiert:", value=text_result, height=200)

            except Exception as e:
                st.error(f"Fehler: {e}")

# 4. History (Damit man sieht, dass es in der DB ist)
st.divider()
st.subheader("📜 Letzte Uploads (aus Supabase)")
if st.button("History aktualisieren"):
    response = supabase.table("transcriptions").select("*").order("created_at", desc=True).limit(5).execute()
    for entry in response.data:
        with st.expander(f"Datei: {entry['filename']}"):
            st.write(entry['content'])