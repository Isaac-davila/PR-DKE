import streamlit as st
from views import render_ui, render_sidebar_history
from ai_service import transcribe_audio
from database import save_to_supabase, get_transcription_history

# START
# streamlit run app.py

#COMMIT
# git add .
# git commit -m "Refactoring: App modularisiert in database, ai_service und views"
# git push origin main

# 1. History laden für die Sidebar
history_data = get_transcription_history(limit=15)
selected_old_chat = render_sidebar_history(history_data)

# 2. Haupt-UI rendern
selected_action, uploaded_file = render_ui()

# 3. Logik: Zeige entweder den ausgewählten alten Chat ODER den neuen Upload
if selected_old_chat:
    st.divider()
    st.subheader(f"Historie: {selected_old_chat['filename']}")
    st.info(f"Aktion: {selected_action}")  # Zeigt die aktuell gewählte Aktion an
    st.write(selected_old_chat['content'])

elif uploaded_file is not None:
    st.audio(uploaded_file)

    if st.button(f"{selected_action} starten"):
        with st.spinner(f"KI arbeitet: {selected_action}..."):
            try:
                text_result = transcribe_audio(uploaded_file)
                # Hier könnte man je nach 'selected_action' den Text noch bearbeiten

                save_to_supabase(uploaded_file.name, text_result)
                st.success("Erledigt!")
                st.write(text_result)
                st.rerun()  # Damit der neue Eintrag sofort in der Sidebar erscheint
            except Exception as e:
                st.error(f"Fehler: {e}")