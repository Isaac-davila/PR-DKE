import streamlit as st
import os
from groq import Groq  # <--- Hier nutzen wir jetzt groq
from dotenv import load_dotenv

load_dotenv()
# Client für Groq aufsetzen
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.title("DKE Agent (Kostenlose Version via Groq)")

uploaded_file = st.file_uploader("Lade MP3 hoch", type=["mp3"])

if uploaded_file is not None:
    st.audio(uploaded_file)

    if st.button("Text extrahieren"):
        with st.spinner("Groq Whisper arbeitet blitzschnell..."):
            try:
                # Datei für Groq vorbereiten
                file_content = uploaded_file.read()

                # Transkription via Groq
                transcription = client.audio.transcriptions.create(
                    file=("filename.mp3", file_content),
                    model="whisper-large-v3",  # Groq nutzt das beste Whisper Modell
                    response_format="json"
                )

                st.success("Fertig!")
                st.text_area("Ergebnis:", value=transcription.text, height=300)

            except Exception as e:
                st.error(f"Fehler: {e}")