import streamlit as st
import time
from views.views import render_ui, render_sidebar_history
from ai_service import process_with_ai_action
from ai_service import transcribe_audio
from database import (
    supabase,
    save_to_supabase,
    update_transcription_entry,
    get_transcription_history,
    get_current_user,
    login_with_google,
    logout,
    is_admin,
    has_role
)
from views.admin_view import render_admin_view


def main():
    st.set_page_config(page_title="DKE Audio Agent", layout="wide")

    if "user" not in st.session_state:
        st.session_state.user = None
    if "view" not in st.session_state:
        st.session_state.view = "main"

    if "current_transcript" not in st.session_state: st.session_state.current_transcript = None
    if "current_filename" not in st.session_state: st.session_state.current_filename = None
    if "current_results" not in st.session_state: st.session_state.current_results = []
    if "current_entry_id" not in st.session_state: st.session_state.current_entry_id = None

    # Token Exchange
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

    user = st.session_state.user or get_current_user()

    if not user:
        st.title("🎙️ DKE Audio Agent")
        st.info("Bitte melde dich an.")
        if st.button("Mit Google anmelden"):
            auth_url = login_with_google()
            st.write(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.stop()
        return

    st.session_state.user = user
    user_is_admin = is_admin(user.id) or user.email == "isaac.davila.mendez@gmail.com"

    with st.sidebar:
        st.subheader("Konto")
        st.write(f"👤 {user.email}")

        # Zeige Admin Konsole nur für Admins
        if user_is_admin:
            if st.button("⚙️ Admin-Konsole"):
                st.session_state.view = "admin"
                st.rerun()

        if st.session_state.view != "main":
            if st.button("🏠 Zurück"):
                st.session_state.view = "main"
                st.rerun()

        if st.button("Abmelden"):
            logout()
            st.session_state.user = None
            st.rerun()

        st.divider()
        # Historie laden (Logik für Admin/Basic ist in database.py)
        history_data = get_transcription_history(user_id=user.id, limit=15)
        selected_old_chat = render_sidebar_history(history_data)

    if st.session_state.view == "admin" and user_is_admin:
        render_admin_view(user)
    else:
        selected_action, uploaded_file = render_ui()
        if selected_old_chat:
            st.divider()
            st.subheader(f"Historie: {selected_old_chat['filename']}")
            st.write(selected_old_chat['content'])
        elif uploaded_file:
            st.audio(uploaded_file)

            if st.button(f"{selected_action} starten"):
                with st.spinner("KI arbeitet..."):
                    try:
                        st.session_state.current_filename = []
                        st.session_state.current_entry_id = None
                        transcript = transcribe_audio(uploaded_file)
                        st.session_state.current_transcript = transcript
                        st.session_state.current_filename = uploaded_file.name
                        text_result, ai_tags = process_with_ai_action(transcript, selected_action)
                        result = save_to_supabase(uploaded_file.name, text_result, user.id, transcript, ai_tags)
                        if(result.data and len(result.data) > 0):
                            st.session_state.current_entry_id = result.data[0]["id"]
                        st.session_state.current_results.append({"action": selected_action,"result": text_result})
                        st.success("Erledigt!")
                        st.write(text_result)
                    except Exception as e:
                        st.error(f"Fehler: {e}")
        if st.session_state.current_transcript:
            st.divider()
            st.subheader("Aktueller Chat")
            if st.session_state.current_filename:
                st.caption(f"Datei: {st.session_state.current_filename}")
            for item in st.session_state.current_results:
                st.write(f"**{item['action']}**")
                st.write(item["result"])
            followup_action = st.selectbox("Weitere Aktion auf aktuelles Transkript anwenden",
                ["Zusammenfassen", "Wichtige Punkte extrahieren"],
                key="current_followup_action" )
            if st.button("Weiter mit aktuellem Chat"):
                with st.spinner("KI arbeitet..."):
                    try:
                        text_result, ai_tags = process_with_ai_action(st.session_state.current_transcript, followup_action)
                        if st.session_state.current_entry_id:
                            update_transcription_entry(st.session_state.current_entry_id, text_result, tag_ids=ai_tags)
                        st.session_state.current_results.append({"action": followup_action, "result": text_result})
                        st.success("Neues Ergebnis erstellt!")
                        st.write(text_result)
                    except Exception as e:
                        st.error(f"Fehler: {e}")
if __name__ == "__main__":
    main()