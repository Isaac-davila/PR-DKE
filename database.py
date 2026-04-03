import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

@st.cache_resource
def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

supabase = get_supabase_client()

def login_with_google():
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": "http://localhost:8501"}
    })
    return res.url

def get_current_user():
    try:
        session_res = supabase.auth.get_session()
        if session_res and session_res.session:
            return session_res.session.user
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            return user_res.user
    except Exception:
        return None
    return None

def logout():
    supabase.auth.sign_out()

def is_admin(user_id):
    if not user_id: return False
    try:
        res = supabase.table("user_tags").select("tag_id, tags(name)").eq("user_id", user_id).execute()
        for entry in res.data:
            if entry.get("tags", {}).get("name") == "admin": return True
    except Exception: return False
    return False

def save_to_supabase(filename, text_content, user_id, tag_ids=None):
    data = {"filename": filename, "content": text_content, "user_id": user_id, "tag_ids": tag_ids or []}
    return supabase.table("transcriptions").insert(data).execute()

def get_transcription_history(user_id=None, limit=15):
    try:
        query = supabase.table("transcriptions").select("*")
        if user_id: query = query.eq("user_id", user_id)
        res = query.order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        return []

# Admin Funktionen
def get_all_users(): return supabase.table("profiles").select("*").execute().data
def get_all_tags(): return supabase.table("tags").select("*").execute().data
def get_user_tags(user_id):
    res = supabase.table("user_tags").select("tags(name)").eq("user_id", user_id).execute()
    return [item['tags']['name'] for item in res.data if item.get('tags')]
def assign_tag_to_user(user_id, tag_id): return supabase.table("user_tags").insert({"user_id": user_id, "tag_id": tag_id}).execute()
def create_tag(tag_name): return supabase.table("tags").insert({"name": tag_name}).execute()
def remove_tag_from_user(user_id, tag_name):
    tag_res = supabase.table("tags").select("id").eq("name", tag_name).execute()
    if not tag_res.data: return False
    return supabase.table("user_tags").delete().eq("user_id", user_id).eq("tag_id", tag_res.data[0]['id']).execute()