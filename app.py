import streamlit as st
from views import render_ui, render_history
from ai_service import transcribe_audio
from database import save_to_supabase, get_transcription_history


# Start code: streamlit run app.py

# 1. UI rendern
uploaded_file = render_ui()

# 2. Transkriptions-Logik
if uploaded_file is not None:
    st.audio(uploaded_file)

    if st.button("Transkribieren & Speichern"):
        with st.spinner("Whisper KI extrahiert Text..."):
            try:
                # KI Service nutzen
                text_result = transcribe_audio(uploaded_file)

                # Datenbank Service nutzen
                save_to_supabase(uploaded_file.name, text_result)

                st.success("✅ Erfolgreich transkribiert und gespeichert!")
                st.text_area("Extrahiert:", value=text_result, height=200)
            except Exception as e:
                st.error(f"Fehler im Ablauf: {e}")

# 3. History anzeigen
history_data = get_transcription_history()
render_history(history_data)