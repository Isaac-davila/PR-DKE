import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
    return create_client(url, key)


supabase = get_supabase_client()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def login_with_google() -> str:
    res = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {"redirect_to": "http://localhost:8501"},
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
        pass
    return None


def logout():
    supabase.auth.sign_out()


# ---------------------------------------------------------------------------
# Role / permission helpers
# ---------------------------------------------------------------------------

def _get_user_role_names(user_id: str) -> list[str]:
    try:
        res = (
            supabase.table("user_tags")
            .select("tags(name)")
            .eq("user_id", user_id)
            .execute()
        )
        return [item["tags"]["name"] for item in res.data if item.get("tags")]
    except Exception:
        return []


def has_role(user_id: str, roles: list[str] = None) -> bool:
    if not user_id: return False
    roles = roles or ["admin", "basic"]
    user_roles = _get_user_role_names(user_id)
    return any(role in user_roles for role in roles)


def is_admin(user_id: str) -> bool:
    return has_role(user_id, ["admin"])


# ---------------------------------------------------------------------------
# Transcription CRUD
# ---------------------------------------------------------------------------

def get_transcription_history(user_id: str = None, limit: int = 20) -> list[dict]:
    """
    Holt die Historie:
    1. Admins sehen alles.
    2. User sehen eigene Transkripte ODER Transkripte mit passenden Tags.
    """
    try:
        if is_admin(user_id):
            return supabase.table("transcriptions").select("*").order("created_at", desc=True).limit(
                limit).execute().data or []

        # Welche Tags hat der User?
        user_tag_res = supabase.table("user_tags").select("tag_id").eq("user_id", user_id).execute()
        user_tag_ids = [item["tag_id"] for item in user_tag_res.data]

        if user_tag_ids:
            # Shared Logic: Eigene ODER passende Tag-IDs via Array Overlap (.ov)
            tag_filter = f"tag_ids.ov.{{{','.join(map(str, user_tag_ids))}}}"
            res = (
                supabase.table("transcriptions")
                .select("*")
                .or_(f"user_id.eq.{user_id},{tag_filter}")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
        else:
            # Nur eigene Transkripte
            res = supabase.table("transcriptions").select("*").eq("user_id", user_id).order("created_at",
                                                                                            desc=True).limit(
                limit).execute()

        return res.data or []
    except Exception as e:
        st.error(f"Fehler beim Laden der Historie: {e}")
        return []


def save_to_supabase(filename, text_content, user_id, transcript=None, tag_ids=None, audio_path=None):
    clean_ids = [int(tid) for tid in tag_ids] if tag_ids else []
    data = {
        "filename": filename, "content": text_content, "transcript": transcript,
        "user_id": user_id, "tag_ids": clean_ids, "audio_path": audio_path
    }
    return supabase.table("transcriptions").insert(data).execute()


def update_transcription_entry(entry_id: str, text_content: str, tag_ids: list = None):
    clean_ids = [int(tid) for tid in tag_ids] if tag_ids else []
    return (
        supabase.table("transcriptions")
        .update({"content": text_content, "tag_ids": clean_ids})
        .eq("id", entry_id)
        .execute()
    )


# ---------------------------------------------------------------------------
# Admin / tag management
# ---------------------------------------------------------------------------

def get_all_users() -> list[dict]:
    try:
        return supabase.table("profiles").select("*").execute().data or []
    except Exception:
        return []


def get_all_tags() -> list[dict]:
    try:
        return supabase.table("tags").select("*").execute().data or []
    except Exception:
        return []


def get_user_tags(user_id: str) -> list[str]:
    return _get_user_role_names(user_id)


def create_tag(tag_name: str):
    if not tag_name: return None
    try:
        return supabase.table("tags").insert({"name": tag_name}).execute()
    except Exception as e:
        if "23505" in str(e): return "exists"
        return None


def assign_tag_to_user(user_id: str, tag_id: int):
    try:
        return supabase.table("user_tags").insert({"user_id": user_id, "tag_id": tag_id}).execute()
    except Exception as e:
        if "23505" in str(e): return None
        raise


def remove_tag_from_user(user_id: str, tag_name: str) -> bool:
    try:
        tag_res = supabase.table("tags").select("id").eq("name", tag_name).execute()
        if not tag_res.data: return False
        tag_id = tag_res.data[0]["id"]
        supabase.table("user_tags").delete().eq("user_id", user_id).eq("tag_id", tag_id).execute()
        return True
    except Exception:
        return False


def delete_tag_globally(tag_id: int):
    supabase.table("user_tags").delete().eq("tag_id", tag_id).execute()
    return supabase.table("tags").delete().eq("id", tag_id).execute()