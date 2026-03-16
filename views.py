import streamlit as st


def render_ui():
    """Zeigt Header und Datei-Uploader an."""
    st.set_page_config(page_title="DKE Audio Intelligence", layout="centered")
    st.title("🎙️ DKE Audio Agent")
    st.info("Transkribiere MP3s und speichere sie direkt in Supabase.")
    return st.file_uploader("MP3 Datei auswählen", type=["mp3"])


def render_history(entries):
    """Zeigt die Liste der letzten Transkriptionen an."""
    st.divider()
    st.subheader("📜 Letzte Uploads (aus Supabase)")

    if st.button("History aktualisieren"):
        st.rerun()  # Einfacher Weg, um die Anzeige neu zu triggern

    if not entries:
        st.write("Noch keine Einträge vorhanden.")
        return

    for entry in entries:
        with st.expander(f"Datei: {entry['filename']}"):
            st.write(entry['content'])
            st.caption(f"Erstellt am: {entry.get('created_at', 'unbekannt')}")