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


# --- AUTHENTIFIZIERUNG ---

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
            user = session_res.session.user
            ensure_basic_tag(user.id)  # Automatisch "basic" zuweisen
            return user
        user_res = supabase.auth.get_user()
        if user_res and user_res.user:
            ensure_basic_tag(user_res.user.id)
            return user_res.user
    except Exception:
        return None
    return None


def ensure_basic_tag(user_id):
    """Prüft ob User einen Tag hat, wenn nicht -> basic."""
    try:
        existing = supabase.table("user_tags").select("*").eq("user_id", user_id).execute()
        if not existing.data:
            # Hol ID vom "basic" tag
            tag_res = supabase.table("tags").select("id").eq("name", "basic").execute()
            if tag_res.data:
                tag_id = tag_res.data[0]['id']
                supabase.table("user_tags").insert({"user_id": user_id, "tag_id": tag_id}).execute()
    except Exception as e:
        print(f"Fehler bei Auto-Tag: {e}")


def logout():
    supabase.auth.sign_out()


def has_role(user_id, roles=["admin", "basic"]):
    """Prüft ob der User eine der übergebenen Rollen hat."""
    if not user_id: return False
    try:
        res = supabase.table("user_tags").select("tags(name)").eq("user_id", user_id).execute()
        user_roles = [item['tags']['name'] for item in res.data if item.get('tags')]
        return any(role in user_roles for role in roles)
    except Exception:
        return False
    return False


def is_admin(user_id):
    return has_role(user_id, ["admin"])


# --- TRANSKRIPTIONEN & HISTORIE ---

def get_transcription_history(user_id=None, limit=15):
    """
    Admins und Basics sehen alles. Andere nur eigene.
    """
    try:
        query = supabase.table("transcriptions").select("*")

        # Wenn KEIN Admin/Basic -> Filter auf eigene user_id
        if not has_role(user_id, ["admin", "basic"]):
            query = query.eq("user_id", user_id)

        res = query.order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        print(f"Fehler History: {e}")
        return []


def save_to_supabase(filename, text_content, user_id, transcript=None, tag_ids=None, audio_path=None):
    data = {"filename": filename, "content": text_content, "transcript": transcript, "user_id": user_id, "tag_ids": tag_ids or [], "audio_path": audio_path}
    return supabase.table("transcriptions").insert(data).execute()


# --- ADMIN FUNKTIONEN ---
def get_all_users(): return supabase.table("profiles").select("*").execute().data


def get_all_tags(): return supabase.table("tags").select("*").execute().data

def get_user_tags(user_id):
    res = supabase.table("user_tags").select("tags(name)").eq("user_id", user_id).execute()
    return [item['tags']['name'] for item in res.data if item.get('tags')]


def assign_tag_to_user(user_id, tag_id): return supabase.table("user_tags").insert(
    {"user_id": user_id, "tag_id": tag_id}).execute()


def create_tag(tag_name, created_by=None): return supabase.table("tags").insert({"name": tag_name}).execute()


def remove_tag_from_user(user_id, tag_name):
    tag_res = supabase.table("tags").select("id").eq("name", tag_name).execute()
    if not tag_res.data: return False
    return supabase.table("user_tags").delete().eq("user_id", user_id).eq("tag_id", tag_res.data[0]['id']).execute()

def update_transcription_entry(entry_id, text_content, tag_ids = None):
    data = {"content": text_content, "tag_ids": tag_ids or []}
    return supabase.table("transcriptions").update(data).eq("id", entry_id).execute()