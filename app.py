import os
import re
import streamlit as st
import datetime
import uuid
import time

from download_service import DownloadService
from pipeline import run_pipeline
from views.views import render_ui, render_sidebar_history, inject_css, render_transcript_content
from ai_service import process_with_ai_action, transcribe_audio, generate_title
from database import (
    supabase,
    save_to_supabase,
    update_transcription_entry,
    get_transcription_history,
    get_current_user,
    login_with_google,
    logout,
    is_admin,
    has_role,
    get_all_tags,
    get_user_tags,
)
from views.admin_view import render_admin_view

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_LOGIN_CSS = """
<style>
/* Versteckt die Sidebar auf der Login-Seite */
[data-testid="stSidebar"] { display: none !important; }

/* TRICK: Wir machen den gesamten Streamlit-Container zur weißen Karte! */
.block-container { 
    max-width: 440px !important; 
    margin-top: 12vh !important;
    background: #ffffff !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    padding: 3.5rem 2.75rem 2.5rem !important;
    box-shadow: 0 4px 32px rgba(74,63,143,0.10) !important;
    text-align: center !important;
}

.login-logo { font-size: 3.5rem; line-height: 1; margin-bottom: 0.75rem; }
.login-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 0.4rem;
    font-family: var(--font);
}
.login-sub {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    font-family: var(--font);
    line-height: 1.5;
}
.login-divider { height: 1px; background: var(--border); margin: 1.75rem 0 1.5rem; }

/* Override the global button style for the Google button only */
[data-testid="stButton"] > button {
    width: 100% !important;
    background: #ffffff !important;
    color: #3c3c3c !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.72rem 1.5rem !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07) !important;
    transition: box-shadow 0.2s, border-color 0.2s !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 1.5rem !important; /* Abstand zum Footer */
}
[data-testid="stButton"] > button:hover {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 3px 12px rgba(74,63,143,0.18) !important;
}
.login-footer {
    font-size: 0.73rem;
    color: var(--text-muted);
    font-family: var(--font);
    line-height: 1.6;
}
</style>
"""

def render_login_page():
    """Renders the centered login card and handles the Google OAuth redirect."""
    st.markdown(_LOGIN_CSS, unsafe_allow_html=True)

    # Die HTML-Elemente liegen jetzt direkt im weißen .block-container
    st.markdown("""
    <div class="login-logo">🎙️</div>
    <div class="login-title">DKE Audio Agent</div>
    <div class="login-sub">
        Transkription, Diarisierung und<br>KI-Analyse für Audiodateien.
    </div>
    <div class="login-divider"></div>
    """, unsafe_allow_html=True)

    # Der Button liegt jetzt ganz natürlich zwischen Divider und Footer innerhalb der Box
    if st.button("Mit Google anmelden", key="google_login"):
        auth_url = login_with_google()
        st.write(
            f'<meta http-equiv="refresh" content="0;url={auth_url}">',
            unsafe_allow_html=True,
        )
        st.stop()

    st.markdown("""
    <div class="login-footer">
        Durch die Anmeldung stimmst du den Nutzungsbedingungen zu.<br>
        Deine Daten werden sicher in Supabase gespeichert.
    </div>
    """, unsafe_allow_html=True)

def handle_auth():
    """Handles OAuth callback and session restoration. Returns user or None."""
    if "code" in st.query_params:
        auth_code = st.query_params["code"]
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            if res and res.user:
                st.session_state.user = res.user
        except Exception:
            check = get_current_user()
            if check:
                st.session_state.user = check
        st.query_params.clear()
        st.rerun()

    user = st.session_state.get("user") or get_current_user()
    if not user:
        render_login_page()
        return None
    return user


# ---------------------------------------------------------------------------
# Download & Tag Management Helpers
# ---------------------------------------------------------------------------

def render_download_section(title: str, filename: str, content: str, key_suffix: str):
    """Renders download options for a transcript or result."""
    st.divider()
    st.subheader("Download")
    formats = DownloadService.get_available_formats()
    format_choice = st.selectbox(
        f"Format ({title})", formats, key=f"fmt_{key_suffix}"
    )
    timestamp = DownloadService.get_timestamp()
    markdown_content = (
        f"# {title}\n\n"
        f"**Datei:** {filename}\n"
        f"**Erstellt am:** {timestamp}\n\n"
        f"---\n\n{content}"
    )
    file_data, file_name, mime = DownloadService.generate_file(
        markdown_content=markdown_content,
        format_choice=format_choice,
        filename=os.path.splitext(filename)[0],
        prefix=DownloadService.sanitize_filename(title),
        title=title,
    )
    st.download_button(
        label=f"Als {format_choice} herunterladen",
        data=file_data,
        file_name=file_name,
        mime=mime,
        key=f"btn_{key_suffix}",
    )


def render_tag_manager(entry_id: int, current_content: str, current_tag_ids: list):
    """Renders a standalone UI to manage tags for a specific transcription entry."""
    st.divider()
    st.subheader("🏷️ Tags verwalten")
    st.caption("Füge Tags hinzu, um dieses Dokument mit deinem Team zu teilen oder besser zu filtern.")

    all_tags = get_all_tags()
    if not all_tags:
        st.info("Keine Tags im System vorhanden. Ein Admin kann neue Tags erstellen.")
        return

    # Map names to IDs and IDs to names
    tag_options = {t["name"]: int(t["id"]) for t in all_tags}
    id_to_name = {int(t["id"]): t["name"] for t in all_tags}

    # Find the current names from the IDs saved in DB
    default_names = [id_to_name[tid] for tid in (current_tag_ids or []) if tid in id_to_name]

    with st.form(key=f"tag_form_{entry_id}"):
        sel_names = st.multiselect(
            "Zugewiesene Tags:",
            options=list(tag_options.keys()),
            default=default_names
        )
        submit = st.form_submit_button("Tags speichern")

        if submit:
            new_tag_ids = [tag_options[n] for n in sel_names]
            update_transcription_entry(entry_id, current_content, tag_ids=new_tag_ids)
            st.success("Tags erfolgreich aktualisiert!")

            # Update session state if we are working on the current upload
            if st.session_state.get("current_entry_id") == entry_id:
                st.session_state.current_tag_ids = new_tag_ids

            time.sleep(1)
            st.rerun()


# ---------------------------------------------------------------------------
# Speaker renaming view
# ---------------------------------------------------------------------------

def render_speaker_rename_view(user):
    """
    Shown after diarization when multiple speakers are detected.
    Lets the user name each speaker before saving.
    """
    pending = st.session_state.pending_rename

    st.subheader("Sprecher benennen")
    st.caption(f"Datei: {pending['filename']}")
    st.info("Die KI hat mehrere Sprecher erkannt. Gib jedem einen Namen:")

    speaker_names = {}
    for speaker in pending["speakers"]:
        speaker_names[speaker] = st.text_input(
            f"Name fuer {speaker}", value=speaker, key=f"spk_{speaker}"
        )

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("Namen bestaetigen und verarbeiten", type="primary"):
            with st.spinner("KI arbeitet..."):
                try:
                    transcript = pending["transcript"]
                    for original, name in speaker_names.items():
                        transcript = transcript.replace(original, name)

                    text_result, ai_tags = process_with_ai_action(
                        transcript, pending["action"]
                    )

                    # NEU: Hole alle Tags des Nutzers und weise sie dem Transkript zu
                    all_system_tags = get_all_tags()
                    tag_options = {t["name"]: int(t["id"]) for t in all_system_tags} if all_system_tags else {}
                    user_tag_names = get_user_tags(user.id)
                    user_tag_ids = [tag_options[n] for n in user_tag_names if n in tag_options]

                    final_tag_ids = list(set(user_tag_ids + (ai_tags or [])))

                    result = save_to_supabase(
                        pending["filename"],
                        text_result,
                        user.id,
                        transcript,
                        final_tag_ids,
                        pending["audio_path"],
                        speaker_mapping=speaker_names,
                    )

                    if result.data:
                        st.session_state.current_entry_id = result.data[0]["id"]
                        st.session_state.current_tag_ids = final_tag_ids

                    st.session_state.current_transcript = transcript
                    st.session_state.current_filename = pending["filename"]
                    st.session_state.current_results = [
                        {"action": pending["action"], "result": text_result}
                    ]
                    st.session_state.last_result = text_result
                    st.session_state.last_filename = pending["filename"]
                    st.session_state.last_action = pending["action"]
                    st.session_state.pending_rename = None
                    st.success("Erledigt!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler: {e}")

    with col_cancel:
        if st.button("Abbrechen"):
            st.session_state.pending_rename = None
            st.rerun()


# ---------------------------------------------------------------------------
# History detail view
# ---------------------------------------------------------------------------

def render_history_view(entry: dict):
    """Shows the full content of a previously saved transcript and allows custom chat queries."""
    st.subheader(f"{entry['filename']}")

    # Hier wird die gesamte Historie gerendert
    render_transcript_content(entry["content"])

    st.divider()
    st.subheader("💬 Frage an dieses Transkript stellen")
    st.caption(
        "Nutze das Textfeld, um eine eigene Query abzusenden (z. B. 'Gib mir alle Personen, die genannt wurden').")

    with st.form(key=f"hist_form_{entry['id']}", clear_on_submit=True):
        custom_query = st.text_input(
            "Deine Anweisung / Frage",
            placeholder="Schreibe hier deine Query..."
        )
        submit_btn = st.form_submit_button("Senden")

    if submit_btn:
        if not custom_query.strip():
            st.warning("Bitte gib zuerst eine Query ein.")
        else:
            with st.spinner("KI analysiert..."):
                try:
                    # Original-Transkript nutzen
                    source_text = entry.get("transcript") or entry.get("content")

                    text_result, ai_tags = process_with_ai_action(
                        source_text, custom_query
                    )

                    # Neuen Content zusammenbauen
                    new_content = (
                            entry["content"] +
                            f"\n\n---\n\n**❓ Deine Query:** *{custom_query}*\n\n**🤖 Antwort:**\n{text_result}"
                    )

                    # Versuch in Supabase zu speichern (alte Tags werden beibehalten!)
                    res = update_transcription_entry(
                        entry["id"],
                        new_content,
                        tag_ids=entry.get("tag_ids", [])
                    )

                    if res and hasattr(res, 'data') and len(res.data) > 0:
                        st.success("Erfolgreich! Antwort wurde in der Datenbank gespeichert.")
                    else:
                        st.error(
                            "🚨 KI hat geantwortet, ABER Supabase hat das Speichern blockiert! (RLS-Policy für UPDATE prüfen)")

                    entry["content"] = new_content
                    time.sleep(1.5)
                    st.rerun()

                except Exception as e:
                    st.error(f"Fehler bei der Ausführung: {e}")

    # Tag Manager für historische Einträge
    render_tag_manager(entry["id"], entry["content"], entry.get("tag_ids", []))

    # Download Bereich
    render_download_section("Historie", entry["filename"], entry["content"], f"hist_{entry['id']}")


# ---------------------------------------------------------------------------
# Main upload view
# ---------------------------------------------------------------------------

def render_upload_view(user):
    """Main view: file upload, pipeline selection, processing."""
    selected_action, uploaded_file, pipeline_mode = render_ui()

    if not uploaded_file:
        if st.session_state.get("last_result"):
            render_download_section(
                st.session_state.last_action,
                st.session_state.last_filename,
                st.session_state.last_result,
                "last_result",
            )
        return

    st.audio(uploaded_file)

    if st.button(f"{selected_action} starten", key="start_btn"):
        with st.spinner("KI verarbeitet Audio..."):
            try:
                st.session_state.current_transcript = None
                st.session_state.current_filename = None
                st.session_state.current_entry_id = None
                st.session_state.current_tag_ids = []
                st.session_state.current_results = []

                safe_name = DownloadService.sanitize_filename(uploaded_file.name)
                audio_path = f"{user.id}/{uuid.uuid4()}_{safe_name}.mp3"
                supabase.storage.from_("audio-files").upload(
                    audio_path, uploaded_file.getvalue()
                )
                uploaded_file.seek(0)

                transcript = run_pipeline(uploaded_file, pipeline_mode)

                # Identifizieren mehrerer Sprecher
                speakers = list(set(re.findall(r"SPEAKER_\w+", transcript)))

                if len(speakers) > 1:
                    st.session_state.pending_rename = {
                        "transcript": transcript,
                        "filename": uploaded_file.name,
                        "action": selected_action,
                        "audio_path": audio_path,
                        "speakers": speakers,
                    }
                    st.rerun()
                else:
                    ai_title = generate_title(transcript)
                    now_str = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M")
                    metadata_header = (
                        f"### Metadaten\n"
                        f"- **KI-Titel:** {ai_title}\n"
                        f"- **Originaldatei:** {uploaded_file.name}\n"
                        f"- **Aufnahmezeitpunkt:** {now_str}\n"
                        f"- **Pipeline-Modus:** {pipeline_mode}\n\n---\n\n"
                    )

                    text_result, ai_tags = process_with_ai_action(
                        transcript, selected_action
                    )
                    final_content = metadata_header + text_result

                    # AUTOMATISCHES TAGGING: Holt alle Tags des Nutzers und weist sie dem Transkript zu
                    all_system_tags = get_all_tags()
                    tag_options = {t["name"]: int(t["id"]) for t in all_system_tags} if all_system_tags else {}
                    user_tag_names = get_user_tags(user.id)
                    user_tag_ids = [tag_options[n] for n in user_tag_names if n in tag_options]

                    # Kombiniere User-Tags mit eventuellen KI-Tags
                    final_tag_ids = list(set(user_tag_ids + (ai_tags or [])))

                    result = save_to_supabase(
                        ai_title, final_content, user.id,
                        transcript, final_tag_ids, audio_path
                    )

                    if result.data:
                        st.session_state.current_entry_id = result.data[0]["id"]
                        st.session_state.current_tag_ids = final_tag_ids

                    st.session_state.current_transcript = transcript
                    st.session_state.current_filename = ai_title
                    st.session_state.current_results = [
                        {"action": selected_action, "result": final_content}
                    ]
                    st.session_state.last_result = final_content
                    st.session_state.last_filename = ai_title
                    st.session_state.last_action = selected_action
                    st.success(f"Erfolgreich verarbeitet: {ai_title}")
                    st.rerun()

            except Exception as e:
                st.error(f"Fehler: {e}")

    # Aktuelle Ergebnisse & Follow-up Chat
    if st.session_state.get("current_transcript"):

        for item in st.session_state.get("current_results", []):
            st.write(f"**{item['action']}**")
            render_transcript_content(item["result"])

        st.divider()
        st.subheader("💬 Frage an dieses Transkript stellen")
        if st.session_state.get("current_filename"):
            st.caption(f"Datei: {st.session_state.current_filename}")

        with st.form(key="followup_form", clear_on_submit=True):
            followup_action = st.text_input(
                "Eigene Anweisung eingeben",
                placeholder="z. B. Extrahiere alle erwähnten Deadlines..."
            )
            submit_followup = st.form_submit_button("Ausführen")

        if submit_followup:
            if not followup_action.strip():
                st.warning("Bitte gib eine Query ein.")
            else:
                with st.spinner("KI arbeitet..."):
                    try:
                        text_result, ai_tags = process_with_ai_action(
                            st.session_state.current_transcript, followup_action
                        )
                        formatted_section = f"### 💬 Query: {followup_action}\n\n{text_result}"

                        if st.session_state.get("current_entry_id"):
                            current_content = st.session_state.get("last_result", "")
                            new_content = current_content + f"\n\n---\n\n{formatted_section}"

                            update_transcription_entry(
                                st.session_state.current_entry_id,
                                new_content,
                                tag_ids=st.session_state.get("current_tag_ids", []),
                                # Verhindert Überschreiben alter Tags
                            )
                            st.session_state.last_result = new_content
                        else:
                            st.session_state.last_result = formatted_section

                        st.session_state.current_results.append(
                            {"action": followup_action, "result": text_result}
                        )
                        st.success("Ausgeführt!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")

        # Tag Manager für neue Uploads
        if st.session_state.get("current_entry_id"):
            render_tag_manager(
                st.session_state.current_entry_id,
                st.session_state.last_result,
                st.session_state.get("current_tag_ids", [])
            )

        render_download_section(
            st.session_state.last_action,
            st.session_state.last_filename,
            st.session_state.last_result,
            "current_result",
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="DKE Audio Agent", layout="wide")

    inject_css()

    for key, default in {
        "user": None,
        "view": "main",
        "current_transcript": None,
        "current_filename": None,
        "current_results": [],
        "current_entry_id": None,
        "current_tag_ids": [],
        "pending_rename": None,
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    user = handle_auth()
    if not user:
        return

    st.session_state.user = user
    user_is_admin = is_admin(user.id)

    # --- Sidebar ---
    with st.sidebar:
        st.subheader("Konto")
        st.write(f"{user.email}")

        if user_is_admin:
            if st.button("Admin-Konsole"):
                st.session_state.view = "admin"
                st.rerun()

        if st.session_state.view != "main":
            if st.button("Zurück"):
                st.session_state.view = "main"
                st.session_state.selected_history_id = None
                st.rerun()

        if st.button("Abmelden"):
            logout()
            st.session_state.user = None
            st.rerun()

        st.divider()
        st.subheader("Verlauf")

        if st.button("📝 Neues Transkript", type="primary", use_container_width=True):
            st.session_state.view = "main"
            st.session_state.selected_history_id = None
            st.session_state.current_transcript = None
            st.session_state.current_filename = None
            st.session_state.current_results = []
            st.session_state.current_entry_id = None
            st.session_state.current_tag_ids = []
            st.session_state.last_result = None
            st.rerun()

        history_data = get_transcription_history(user_id=user.id, limit=15)
        selected_old = render_sidebar_history(history_data)

    # --- View routing ---
    if st.session_state.view == "admin" and user_is_admin:
        render_admin_view(user)

    elif selected_old and st.session_state.view != "admin":
        render_history_view(selected_old)

    elif st.session_state.get("pending_rename"):
        render_speaker_rename_view(user)

    else:
        render_upload_view(user)


if __name__ == "__main__":
    main()