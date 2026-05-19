import streamlit as st
import re

# ---------------------------------------------------------------------------
# CSS — NotebookLM-inspired LIGHT theme
# ---------------------------------------------------------------------------

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600&family=Google+Sans+Mono&display=swap');

/* ── Root tokens — light ── */
:root {
    --bg-base:       #f8f8fc;
    --bg-surface:    #f0eff5;
    --bg-elevated:   #e8e7f0;
    --bg-hover:      #e2e0ec;
    --accent:        #4a3f8f;
    --accent-soft:   #ede9ff;
    --accent-dim:    #7c6fa8;
    --text-primary:  #1c1b2e;
    --text-secondary:#4a4760;
    --text-muted:    #8e8aa8;
    --border:        #dddbe8;
    --border-light:  #ccc9dc;
    --success:       #2e7d32;
    --error:         #c62828;
    --radius-sm:     8px;
    --radius-md:     12px;
    --radius-lg:     20px;
    --shadow:        0 2px 12px rgba(0,0,0,0.08);
    --font:          'Google Sans', 'Segoe UI', sans-serif;
    --font-mono:     'Google Sans Mono', monospace;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: var(--font) !important;
}

[data-testid="stHeader"] { background: var(--bg-base) !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Sidebar history buttons */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: var(--text-secondary) !important;
    text-align: left !important;
    padding: 10px 12px !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.85rem !important;
    font-family: var(--font) !important;
    transition: background 0.15s, color 0.15s !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--bg-hover) !important;
    color: var(--text-primary) !important;
}

/* Spezielles Design nur für den "Neues Transkript" Button (Primary) in der Sidebar */
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background-color: var(--accent-soft) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent-dim) !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
    justify-content: flex-start !important;
    padding-left: 12px !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    background-color: var(--bg-elevated) !important;
}

/* ── Main content area ── */
.block-container {
    max-width: 860px !important;
    padding: 2.5rem 2rem !important;
}

/* ── Page title ── */
h1 {
    font-size: 2rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.25rem !important;
}
h2, h3 { color: var(--text-primary) !important; font-weight: 500 !important; }

/* ── Upload drop zone ── */
[data-testid="stFileUploader"] {
    background: #ffffff !important;
    border: 1.5px dashed var(--border-light) !important;
    border-radius: var(--radius-md) !important;
    padding: 1.5rem !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--accent-dim) !important;
}
[data-testid="stFileUploader"] * { color: var(--text-secondary) !important; }
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: var(--text-muted) !important;
    font-size: 0.85rem !important;
}

/* ── Selectbox / dropdowns ── */
[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

/* ── Radio buttons (pipeline selector) ── */
[data-testid="stRadio"] {
    background: #ffffff !important;
    border-radius: var(--radius-md) !important;
    padding: 0.75rem 1rem !important;
    border: 1px solid var(--border) !important;
    width: 100% !important; /* NEU: Nimmt die volle Breite der Spalte ein */
    box-sizing: border-box !important;
}
[data-testid="stRadio"] label {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
    cursor: pointer !important;
    width: 100% !important; /* NEU: Macht auch den Klick-Bereich breiter */
}
[data-testid="stRadio"] label:hover { color: var(--text-primary) !important; }

/* 3. Option (Lokale CPU Pipeline) ausgrauen & unklickbar machen */
[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(3) {
    opacity: 0.4 !important;
    pointer-events: none !important;
    cursor: not-allowed !important;
    filter: grayscale(100%);
}

/* ── Buttons ── */
.stButton > button {
    background: var(--accent-soft) !important;
    color: var(--accent) !important;
    border: 1px solid var(--accent-dim) !important;
    border-radius: var(--radius-lg) !important;
    font-family: var(--font) !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.4rem !important;
    transition: background 0.2s, box-shadow 0.2s !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    background: var(--bg-elevated) !important;
    box-shadow: 0 0 0 1px var(--accent-dim) !important;
}

/* ── Multiselect tags ── */
[data-testid="stMultiSelect"] > div {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
}
span[data-baseweb="tag"] {
    background: var(--accent-soft) !important;
    border-radius: 99px !important;
    color: var(--accent) !important;
    font-size: 0.8rem !important;
}

/* ── Text inputs ── */
[data-testid="stTextInput"] input {
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 2px var(--accent-soft) !important;
}

/* ── Spinner & status messages ── */
[data-testid="stSpinner"] * { color: var(--accent) !important; }
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border: none !important;
    font-size: 0.875rem !important;
}

/* ── Audio player ── */
audio {
    width: 100% !important;
    border-radius: var(--radius-sm) !important;
    margin: 0.5rem 0 !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Caption / muted text ── */
[data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
}
</style>
"""


def inject_css():
    """Injects the shared NotebookLM-inspired light stylesheet. Call once per page."""
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Transcript formatter
# ---------------------------------------------------------------------------

def format_transcript(text: str) -> str:
    """
    Converts inline diarization format:
        [Teacher @ 10.2s] Good morning. [Student @ 15.1s] Hello.

    Into clean speaker-per-line format:
        **Teacher:** Good morning.
        **Student:** Hello.
    """
    pattern = re.compile(r'\[([^\]@]+?)(?:\s*@\s*[\d.]+s)?\]\s*')
    parts = pattern.split(text.strip())

    if len(parts) <= 1:
        return text

    lines = []
    i = 1
    while i < len(parts) - 1:
        speaker = parts[i].strip()
        utterance = parts[i + 1].strip()
        if utterance:
            lines.append(f"**{speaker}:** {utterance}")
        i += 2

    return "\n\n".join(lines) if lines else text


def render_transcript_content(text: str):
    """
    Renders transcript content with proper speaker formatting.
    """
    formatted = format_transcript(text)
    st.markdown(formatted)


# ---------------------------------------------------------------------------
# Main UI — upload panel + pipeline selector
# ---------------------------------------------------------------------------

def render_ui() -> tuple:
    """
    Renders the main upload UI with a modern, step-by-step workflow.
    Returns: (action, uploaded_file, mode)
    """
    st.markdown("## 🎙️ DKE Audio Agent")
    st.markdown(
        "<p style='color:var(--text-muted);font-size:0.95rem;margin-top:-0.5rem;margin-bottom:2rem;'>"
        "Lade eine Audiodatei hoch und konfiguriere die KI-Analyse."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── 1. Upload Section (Volle Breite für Drag & Drop) ──
    st.markdown(
        "<p style='font-size:0.78rem;font-weight:600;color:var(--text-muted);letter-spacing:0.08em;margin-bottom:8px;'>"
        "1. AUDIODATEI HINZUFÜGEN</p>",
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader(
        "MP3 hochladen",
        type=["mp3"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

    # ── 2. Settings Section (Zwei Spalten: Modus -> Aktion) ──
    col_mode, col_action = st.columns(2, gap="large")

    with col_mode:
        st.markdown(
            "<p style='font-size:0.78rem;font-weight:600;color:var(--text-muted);letter-spacing:0.08em;margin-bottom:8px;'>"
            "2. PIPELINE-MODUS</p>",
            unsafe_allow_html=True,
        )
        mode = st.radio(
            "Pipeline",
            options=["groq", "assemblyai", "groq_local"],
            format_func=lambda x: {
                "groq": "Transkription",
                "assemblyai": "Diarisierung",
                "groq_local": "💻 Lokal (CPU, sehr langsam)",
            }[x],
            label_visibility="collapsed",
        )

    with col_action:
        st.markdown(
            "<p style='font-size:0.78rem;font-weight:600;color:var(--text-muted);letter-spacing:0.08em;margin-bottom:8px;'>"
            "3. GEWÜNSCHTE AKTION</p>",
            unsafe_allow_html=True,
        )

        if mode == "assemblyai":
            # Bei Diarisierung ist keine andere Aktion möglich
            st.selectbox(
                "Aktion",
                ["Nur Diarisierung"],
                disabled=True,
                label_visibility="collapsed",
            )
            # Im Backend nutzen wir "Transkribieren", damit die KI nicht unnötig manipuliert
            action = "Transkribieren"
        else:
            action_choice = st.selectbox(
                "Aktion",
                ["Transkribieren", "Zusammenfassen", "Wichtige Punkte extrahieren", "Eigener Befehl..."],
                label_visibility="collapsed",
            )

            # Eigene Eingabe einblenden, wenn gewünscht
            if action_choice == "Eigener Befehl...":
                st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
                action = st.text_input(
                    "Dein Befehl",
                    placeholder="Was soll die KI tun?",
                    label_visibility="collapsed"
                )
                # Sicherheits-Fallback falls das Feld leer bleibt
                if not action.strip():
                    action = "Transkribieren"
            else:
                action = action_choice

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    return action, uploaded_file, mode

# ---------------------------------------------------------------------------
# Sidebar history
# ---------------------------------------------------------------------------

def render_sidebar_history(entries: list) -> dict | None:
    """
    Renders transcription history in the sidebar.
    Persists selection across reruns via session_state.

    Returns the selected entry dict or None.
    """
    if not entries:
        st.markdown(
            "<p style='color:var(--text-muted);font-size:0.83rem;padding:0 0.5rem;'>"
            "Noch keine Einträge.</p>",
            unsafe_allow_html=True,
        )
        return None

    if "selected_history_id" not in st.session_state:
        st.session_state.selected_history_id = None

    for entry in entries:
        filename = entry.get("filename", "Unbenannt")
        label = filename[:28] + "…" if len(filename) > 28 else filename
        is_selected = st.session_state.selected_history_id == entry["id"]

        button_style = (
            "background:var(--accent-soft)!important;color:var(--accent)!important;"
            if is_selected else ""
        )
        st.markdown(
            f"<style>#btn_{entry['id']} button {{ {button_style} }}</style>",
            unsafe_allow_html=True,
        )

        if st.button(
            f"📄  {label}",
            key=f"hist_{entry['id']}",
            use_container_width=True,
        ):
            st.session_state.selected_history_id = entry["id"]

    if st.session_state.selected_history_id:
        for entry in entries:
            if entry["id"] == st.session_state.selected_history_id:
                return entry

    return None