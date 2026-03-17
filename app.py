import streamlit as st
from views import render_ui, render_sidebar_history
from ai_service import process_with_ai_action
from database import save_to_supabase, get_transcription_history

# START
# streamlit run app.py

# COMMIT
# git add .
# git commit -m " --- Kommentar--- "
# git push origin main

def main():
    # 1. History laden für die Sidebar
    history_data = get_transcription_history(limit=15)
    selected_old_chat = render_sidebar_history(history_data)

    # 2. Haupt-UI rendern
    selected_action, uploaded_file = render_ui()

    # 3. Logik: Zeige entweder den ausgewählten alten Chat ODER den neuen Upload
    if selected_old_chat:
        st.divider()
        st.subheader(f"Historie: {selected_old_chat['filename']}")
        st.write(selected_old_chat['content'])

    elif uploaded_file is not None:
        st.audio(uploaded_file)

        if st.button(f"{selected_action} starten"):
            with st.spinner(f"KI arbeitet: {selected_action}..."):
                try:
                    text_result = process_with_ai_action(uploaded_file, selected_action)
                    save_to_supabase(uploaded_file.name, text_result)
                    st.success("Erledigt!")
                    st.write(text_result)
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")

if __name__ == "__main__":
    main()