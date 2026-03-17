import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

def save_to_supabase(filename, text_content):
    """Speichert eine neue Transkription in der DB."""
    return supabase.table("Transcriptions").insert({
        "filename": filename,
        "content": text_content
    }).execute()

def get_transcription_history(limit=15):
    """Holt die neuesten Einträge inklusive ID."""
    response = supabase.table("Transcriptions") \
        .select("id, filename, content, created_at") \
        .order("created_at", desc=True) \
        .limit(limit) \
        .execute()
    return response.data