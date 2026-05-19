import os
import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Prompts for each supported LLM action
_ACTION_PROMPTS: dict[str, str] = {
    "Zusammenfassen": "Fasse das folgende Transkript kurz und prägnant zusammen.",
    "Wichtige Punkte extrahieren": "Extrahiere die wichtigsten Kernpunkte aus dem folgenden Text als Aufzählung.",
}


def transcribe_audio(uploaded_file) -> str:
    """Transcribes an audio file using Groq Whisper."""
    file_content = uploaded_file.read()
    transcription = client.audio.transcriptions.create(
        file=(uploaded_file.name, file_content),
        model="whisper-large-v3",
        response_format="json",
    )
    return transcription.text


def generate_title(transcript: str) -> str:
    """
    Generates a short AI title (max 5 words) based on the transcript content.
    Falls back to a timestamp string if the API call fails.
    """
    if not transcript:
        return "Unbenanntes Transkript"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Erstelle einen sehr kurzen, prägnanten Titel (maximal 5 Wörter) "
                        "für dieses Transkript. Antworte NUR mit dem Titel, "
                        "keine Anführungszeichen, keine Erklärungen."
                    ),
                },
                {"role": "user", "content": transcript[:1500]},
            ],
        )
        return completion.choices[0].message.content.strip().replace('"', "")
    except Exception:
        return f"Transkript vom {datetime.datetime.now().strftime('%d.%m.%Y, %H:%M')}"


def process_with_ai_action(
    transcript: str,
    action: str,
    available_tags: list = None,
) -> tuple[str, list]:
    if action == "Transkribieren":
        return transcript, []

    # GANZ WICHTIG: Hier muss als Fallback 'action' stehen, nicht der Standard-Satz!
    system_prompt = _ACTION_PROMPTS.get(action, action)

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript},
            ],
        )
        return completion.choices[0].message.content, []
    except Exception as e:
        return f"Fehler bei der KI-Verarbeitung: {e}", []