import os
import streamlit as st
import uuid
import time
import datetime

from download_service import DownloadService
from pipeline import run_pipeline
from views.views import render_ui, render_sidebar_history
from ai_service import process_with_ai_action, generate_title
from database import (
    supabase,
    save_to_supabase,
    update_transcription_entry,
    get_transcription_history,
    get_current_user,
    login_with_google,
    logout,
    is_admin,
    get_all_tags,
)
from views.admin_view import render_admin_view


# --- AUTHENTICATION ---
def handle_auth():
    if "code" in st.query_params:
        auth_code = st.query_params["code"]
        try:
            res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            if res and res.user:
                st.session_state.user = res.user
        except Exception:
            check = get_current_user()
            if check: st.session_state.user = check
        st.query_params.clear()
        st.rerun()

    user = st.session_state.get("user") or get_current_user()
    if not user:
        st.title("🎙️ DKE Audio Agent")
        st.info("Bitte melde dich an.")
        if st.button("Mit Google anmelden"):
            auth_url = login_with_google()
            st.write(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.stop()
        return None
    return user


# --- VIEWS ---
def render_history_view(selected_old: dict):
    """Detailansicht für ein altes Transkript."""
    st.subheader(f"Historie: {selected_old['filename']}")

    # Tags Management
    st.write("### Tags verwalten")
    all_tags = get_all_tags()
    tag_options = {t["name"]: int(t["id"]) for t in all_tags} if all_tags else {}
    current_tag_ids = [int(tid) for tid in selected_old.get("tag_ids", []) if tid is not None]
    current_tag_names = [name for name, tid in tag_options.items() if tid in current_tag_ids]

    new_selected_tags = st.multiselect(
        "Tags bearbeiten:",
        options=list(tag_options.keys()),
        default=current_tag_names,
        key=f"tags_hist_{selected_old['id']}",
    )

    if st.button("Änderungen speichern", key=f"save_tags_{selected_old['id']}"):
        new_tag_ids = [tag_options[name] for name in new_selected_tags if name in tag_options]
        update_transcription_entry(selected_old["id"], selected_old["content"], tag_ids=new_tag_ids)
        st.success("Erfolgreich aktualisiert!")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.write(selected_old["content"])
    render_download_section("Historie", selected_old['filename'], selected_old['content'], f"hist_{selected_old['id']}")


def render_upload_view(user):
    """Standard Upload Ansicht mit KI-Titel und bereinigtem Storage-Upload."""
    action, uploaded_file, mode = render_ui()
    if uploaded_file:
        st.audio(uploaded_file)
        all_tags = get_all_tags()
        tag_options = {t["name"]: int(t["id"]) for t in all_tags} if all_tags else {}
        sel_tags = st.multiselect("Tags zuweisen:", options=list(tag_options.keys()), key="main_upload_tags")

        if st.button(f"{action} starten", key="start_pipeline_btn"):
            with st.spinner("KI generiert Transkript und Titel..."):
                try:
                    # 1. Metadaten & Vorbereitung
                    now_str = datetime.datetime.now().strftime("%d.%m.%Y, %H:%M")
                    orig_filename = uploaded_file.name

                    # Dateinamen für Storage "sicher" machen (entfernt Sonderzeichen wie [ ])
                    safe_storage_filename = DownloadService.sanitize_filename(orig_filename)
                    audio_path = f"{user.id}/{uuid.uuid4()}_{safe_storage_filename}.mp3"

                    # 2. Datei hochladen
                    supabase.storage.from_("audio-files").upload(audio_path, uploaded_file.getvalue())

                    # 3. Transkription & KI-Titel
                    transcript = run_pipeline(uploaded_file, mode)
                    ai_title = generate_title(transcript)

                    # 4. Metadaten-Header zusammenbauen
                    metadata_header = (
                        f"### 📋 Metadaten\n"
                        f"- **Titel:** {ai_title}\n"
                        f"- **Originaldatei:** {orig_filename}\n"
                        f"- **Aufnahmezeitpunkt:** {now_str}\n"
                        f"- **Pipeline-Modus:** {mode}\n\n"
                        f"---\n\n"
                    )

                    # 5. KI-Aktion & Content-Kombination
                    res_text, ai_tags = process_with_ai_action(transcript, action)
                    final_content = metadata_header + res_text

                    # 6. Tags verarbeiten
                    manual_ids = [tag_options[n] for n in sel_tags if n in tag_options]
                    final_tag_ids = list(set(manual_ids + (ai_tags or [])))

                    # 7. Speichern (KI-Titel wird als Filename in der Liste angezeigt)
                    save_to_supabase(ai_title, final_content, user.id, transcript, final_tag_ids, audio_path)

                    st.session_state.last_res = {"text": final_content, "file": ai_title, "action": action}
                    st.success(f"Transkription fertig: {ai_title}")
                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"Fehler bei der Verarbeitung: {e}")

    if st.session_state.get("last_res"):
        lr = st.session_state.last_res
        render_download_section(lr["action"], lr["file"], lr["text"], "last_session_res")


def render_download_section(title, filename, content, key_suffix):
    st.divider()
    st.subheader("📥 Download")
    formats = DownloadService.get_available_formats()
    format_choice = st.selectbox(f"Format ({title})", formats, key=f"fmt_{key_suffix}")
    timestamp = DownloadService.get_timestamp()
    markdown_content = f"# 📄 {title}\n\n**Titel:** {filename}\n**Stand:** {timestamp}\n\n---\n\n{content}"

    file_data, file_name, mime = DownloadService.generate_file(
        markdown_content=markdown_content,
        format_choice=format_choice,
        filename=DownloadService.sanitize_filename(filename),
        prefix=DownloadService.sanitize_filename(title),
        title=title
    )
    st.download_button(f"⬇️ Als {format_choice} laden", file_data, file_name, mime, key=f"btn_{key_suffix}")


# --- MAIN ---
def main():
    st.set_page_config(page_title="DKE Audio Agent", layout="wide")

    if "view" not in st.session_state:
        st.session_state.view = "main"

    user = handle_auth()
    if not user: return

    st.session_state.user = user
    user_is_admin = is_admin(user.id) or user.email == "isaac.davila.mendez@gmail.com"

    with st.sidebar:
        st.subheader("Konto")
        st.write(f"👤 {user.email}")

        if user_is_admin:
            if st.button("⚙️ Admin-Konsole"):
                st.session_state.view = "admin"
                if "selected_history_id" in st.session_state:
                    st.session_state.selected_history_id = None
                st.rerun()

        if st.button("🎙️ Neuer Upload / Home"):
            st.session_state.view = "main"
            if "selected_history_id" in st.session_state:
                st.session_state.selected_history_id = None
            st.rerun()

        if st.button("Abmelden"):
            logout()
            st.session_state.user = None
            st.rerun()

        st.divider()
        st.subheader("📜 Historie")
        history_data = get_transcription_history(user_id=user.id, limit=15)
        selected_old = render_sidebar_history(history_data)

    # Routing
    if selected_old and st.session_state.view != "admin":
        st.session_state.view = "history"
        render_history_view(selected_old)
    elif st.session_state.view == "admin" and user_is_admin:
        render_admin_view(user)
    else:
        render_upload_view(user)


if __name__ == "__main__":
    main()