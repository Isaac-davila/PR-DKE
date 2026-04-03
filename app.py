import streamlit as st
import time
from views.views import render_ui, render_sidebar_history
from ai_service import process_with_ai_action
from database import (
    supabase,
    save_to_supabase,
    get_transcription_history,
    get_current_user,
    login_with_google,
    logout,
    is_admin
)
from views.admin_view import render_admin_view


def main():
    # 1. Konfiguration (Muss zwingend als allererstes stehen)
    st.set_page_config(page_title="DKE Audio Agent", layout="wide")

    # 2. Session State Initialisierung
    if "user" not in st.session_state:
        st.session_state.user = None
    if "view" not in st.session_state:
        st.session_state.view = "main"

    # --- 3. TOKEN-AUSTAUSCH LOGIK (Google Redirect Handling) ---
    if "code" in st.query_params:
        auth_code = st.query_params["code"]
        try:
            # Tauscht den Code bei Supabase gegen eine echte Session ein
            res = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            if res and res.user:
                st.session_state.user = res.user
        except Exception:
            check = get_current_user()
            if check:
                st.session_state.user = check

        # URL bereinigen und App neu starten
        st.query_params.clear()
        st.rerun()

    # Aktuellen User prüfen
    user = st.session_state.user or get_current_user()

    # --- 4. LOGIN LOGIK ---
    if not user:
        st.title("🎙️ DKE Audio Agent")
        st.info("Bitte melde dich an, um den Audio Agent zu nutzen.")
        if st.button("Mit Google anmelden"):
            auth_url = login_with_google()
            st.write(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
            st.stop()
        return

        # --- 5. AUTHENTIFIZIERTER BEREICH ---
    st.session_state.user = user
    user_is_admin = True if user.email == "isaac.davila.mendez@gmail.com" else is_admin(user.id)

    with st.sidebar:
        st.subheader("Konto")
        st.write(f"👤 {user.email}")

        if user_is_admin:
            st.info("🛡️ Admin-Status")
            if st.button("⚙️ Admin-Konsole"):
                st.session_state.view = "admin"
                st.rerun()

        if st.session_state.view != "main":
            if st.button("🏠 Zurück zur App"):
                st.session_state.view = "main"
                st.rerun()

        if st.button("Abmelden"):
            logout()
            st.session_state.user = None
            st.rerun()

        st.divider()
        history_data = get_transcription_history(user_id=user.id, limit=15)
        selected_old_chat = render_sidebar_history(history_data)

    # --- 6. VIEW ROUTING ---
    if st.session_state.view == "admin" and user_is_admin:
        render_admin_view(user)
    else:
        selected_action, uploaded_file = render_ui()

        if selected_old_chat:
            st.divider()
            st.subheader(f"Historie: {selected_old_chat['filename']}")
            st.write(selected_old_chat['content'])
        elif uploaded_file is not None:
            st.audio(uploaded_file)
            if st.button(f"{selected_action} starten"):
                with st.spinner(f"KI arbeitet..."):
                    try:
                        text_result, ai_tags = process_with_ai_action(uploaded_file, selected_action)
                        save_to_supabase(uploaded_file.name, text_result, user.id, ai_tags)
                        st.success("Erledigt!")
                        st.write(text_result)
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Fehler: {e}")


if __name__ == "__main__":
    main()