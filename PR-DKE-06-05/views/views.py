import streamlit as st


def render_ui() -> tuple:
    """
    Renders the main upload UI (title, action selector, file uploader, pipeline mode).

    Returns:
        (action, uploaded_file, mode) tuple.
        - action:        str — selected processing action
        - uploaded_file: UploadedFile | None
        - mode:          str — selected pipeline mode
    """
    st.title("🎙️ DKE Audio Agent")

    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        action = st.selectbox(
            "Was möchtest du tun?",
            ["Transkribieren", "Zusammenfassen", "Wichtige Punkte extrahieren"],
            label_visibility="collapsed",
        )
    with col2:
        uploaded_file = st.file_uploader(
            "Upload Audio", type=["mp3"], label_visibility="collapsed"
        )

    st.caption("🔧 Pipeline-Modus")
    mode = st.radio(
        "Pipeline",
        options=["groq", "groq_local", "assemblyai"],
        format_func=lambda x: {
            "groq": "☁️ Groq (nur Transkription)",
            "groq_local": "💻 Groq + Lokale Diarisierung (CPU, dauert bis zu 5–20× die Dateilänge)",
            "assemblyai": "☁️ AssemblyAI (Transkription + Diarisierung)",
        }[x],
        horizontal=True,
        label_visibility="collapsed",
    )

    return action, uploaded_file, mode


def render_sidebar_history(entries: list) -> dict | None:
    """
    Renders the transcription history list inside the sidebar.

    Uses session_state to persist the selected entry across reruns,
    so the correct entry is still available after a button click triggers
    a rerun.

    Args:
        entries: List of transcription dicts from get_transcription_history().

    Returns:
        The selected history entry dict, or None if nothing is selected.
    """
    if not entries:
        st.write("Keine Einträge.")
        return None

    # Persist selection across reruns via session state
    if "selected_history_id" not in st.session_state:
        st.session_state.selected_history_id = None

    for entry in entries:
        label = f"📄 {entry['filename'][:20]}..."
        if st.button(label, key=f"hist_{entry['id']}", use_container_width=True):
            st.session_state.selected_history_id = entry["id"]

    # Return the full entry dict that matches the stored ID
    if st.session_state.selected_history_id:
        for entry in entries:
            if entry["id"] == st.session_state.selected_history_id:
                return entry

    return None