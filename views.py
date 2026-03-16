import streamlit as st


def render_ui():
    st.set_page_config(page_title="DKE Audio Intelligence", layout="wide")

    # Zentrale Ansicht
    st.title("🎙️ DKE Audio Agent")

    # Container für das neue Interface (Dropdown + Upload Logo)
    col1, col2 = st.columns([0.85, 0.15])

    with col1:
        action = st.selectbox(
            "Was möchtest du mit der Datei tun?",
            ["Transkribieren", "Zusammenfassen", "Wichtige Punkte extrahieren"],
            label_visibility="collapsed"  # Macht es cleaner wie im Bild
        )

    with col2:
        # Simuliertes "Upload-Logo" via File Uploader (Streamlit Standard)
        # Ein reines Icon ist in Streamlit ohne Custom HTML schwer klickbar,
        # daher nutzen wir den Standard-Uploader hier kompakt.
        uploaded_file = st.file_uploader("", type=["mp3"], label_visibility="collapsed")

    return action, uploaded_file


def render_sidebar_history(entries):
    """Erstellt die Historie auf der linken Seite wie ein Chat-Menü."""
    with st.sidebar:
        st.header("Historie")
        st.divider()

        if not entries:
            st.write("Noch keine Chats vorhanden.")
            return None

        # Wir erstellen für jeden Eintrag einen Button, der aussieht wie ein Chat-Link
        selected_entry = None
        for entry in entries:
            # Button-Label ist der Dateiname
            if st.button(f"📄 {entry['filename'][:20]}...", key=entry['id'], use_container_width=True):
                selected_entry = entry

        return selected_entry