import streamlit as st
import time

from pipeline import run_pipeline
from views.views import render_ui, render_sidebar_history
from ai_service import process_with_ai_action
from database import (
    supabase,
    save_to_supabase,
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
        selected_action, uploaded_file, pipeline_mode = render_ui()
        if selected_old_chat:
            st.divider()
            st.subheader(f"Historie: {selected_old_chat['filename']}")
            st.write(selected_old_chat['content'])
        elif uploaded_file:
            st.audio(uploaded_file)
            if st.button(f"{selected_action} starten"):
                with st.spinner("KI arbeitet..."):
                    try:
                        text_result = run_pipeline(uploaded_file, selected_action, pipeline_mode)
                        ai_tags = []
                        save_to_supabase(uploaded_file.name, text_result, user.id, ai_tags)
                        st.success("Erledigt!")
                        st.write(text_result)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")


if __name__ == "__main__":
    main()