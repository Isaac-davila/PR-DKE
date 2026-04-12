import streamlit as st

def render_ui():
    st.title("🎙️ DKE Audio Agent")
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        action = st.selectbox(
            "Was möchtest du tun?",
            ["Transkribieren", "Zusammenfassen", "Wichtige Punkte extrahieren"],
            label_visibility="collapsed"
        )
    with col2:
        uploaded_file = st.file_uploader("", type=["mp3"], label_visibility="collapsed")

        # Pipeline mode selector
    st.caption("🔧 Pipeline-Modus")
    mode = st.radio(
        "Pipeline",
        options=["groq", "groq_local", "assemblyai"],
        format_func=lambda x: {
            "groq":       "☁️ Groq (nur Transkription)",
            "groq_local": "💻 Groq + Lokale Diarisierung (CUDA)",
            "assemblyai": "☁️ AssemblyAI (Transkription + Diarisierung)"
        }[x],
        horizontal=True,
        label_visibility="collapsed"
    )

    return action, uploaded_file, mode

def render_sidebar_history(entries):
    with st.sidebar:
        st.header("Historie")
        st.divider()
        if not entries:
            st.write("Keine Einträge.")
            return None
        selected_entry = None
        for entry in entries:
            if st.button(f"📄 {entry['filename'][:20]}...", key=entry['id'], use_container_width=True):
                selected_entry = entry
        return selected_entry