import streamlit as st
import time

from ai_service import process_with_ai_action
from database import get_transcription_history, get_all_tags, save_to_supabase
from views.views import render_ui, render_sidebar_history

def render_main_app_view(user):
    history = get_transcription_history(user.id)
    selected_old = render_sidebar_history(history)
    action, uploaded_file = render_ui()

    if selected_old:
        st.subheader(f"Historie: {selected_old['filename']}")
        st.write(selected_old['content'])
    elif uploaded_file:
        st.audio(uploaded_file)
        all_tags = get_all_tags()
        tag_options = {t['name']: t['id'] for t in all_tags} if all_tags else {}
        default_tag = ["basic"] if "basic" in tag_options else []

        sel_tags = st.multiselect("Diesem Transkript Tags zuweisen:", options=list(tag_options.keys()), default=default_tag)

        if st.button(f"{action} starten"):
            with st.spinner("KI läuft..."):
                res_text, ai_tag_ids = process_with_ai_action(uploaded_file, action, all_tags)
                manual_ids = [tag_options[n] for n in sel_tags if n in tag_options]
                final_ids = list(set(manual_ids + ai_tag_ids))
                save_to_supabase(uploaded_file.name, res_text, user.id, final_ids)
                st.success("Verarbeitet!")
                st.write(res_text)
                time.sleep(1)
                st.rerun()