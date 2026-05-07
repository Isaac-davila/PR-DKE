import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Prompts for each supported LLM action
_ACTION_PROMPTS: dict[str, str] = {
    "Zusammenfassen": "Fasse den folgenden Text kurz und prägnant zusammen.",
    "Wichtige Punkte extrahieren": "Extrahiere die wichtigsten Kernpunkte aus dem folgenden Text.",
}


def transcribe_audio(uploaded_file) -> str:
    """
    Sends an audio file to Groq Whisper for transcription.

    Args:
        uploaded_file: A Streamlit UploadedFile (or any file-like object with
                       .name and .read()).

    Returns:
        The raw transcript text.
    """
    file_content = uploaded_file.read()
    transcription = client.audio.transcriptions.create(
        file=(uploaded_file.name, file_content),
        model="whisper-large-v3",
        response_format="json",
    )
    return transcription.text


def process_with_ai_action(
    transcript: str,
    action: str,
    available_tags: list = None,
) -> tuple[str, list]:
    """
    Applies an LLM action to an already-transcribed text.

    For "Transkribieren" the transcript is returned as-is.
    For other actions, the appropriate Groq LLM call is made.

    Args:
        transcript:     The text to process (output of run_pipeline / transcribe_audio).
        action:         One of "Transkribieren", "Zusammenfassen",
                        "Wichtige Punkte extrahieren".
        available_tags: Reserved for future auto-tagging logic (currently unused).

    Returns:
        A (result_text, tag_ids) tuple. tag_ids is always [] for now.
    """
    if action == "Transkribieren":
        return transcript, []

    system_prompt = _ACTION_PROMPTS.get(action)
    if not system_prompt:
        raise ValueError(f"Unknown action: '{action}'")

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript},
        ],
    )
    return completion.choices[0].message.content, []

def generate_title(transcript: str) -> str:
    """Erstellt einen kurzen Titel aus dem Transkript."""
    if not transcript:
        return "Leeres Transkript"
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Erstelle einen sehr kurzen, prägnanten Titel (max 5 Wörter) für dieses Transkript. Antworte NUR mit dem Titel."},
                {"role": "user", "content": transcript[:1000]}
            ],
        )
        return completion.choices[0].message.content.strip().replace('"', '')
    except Exception:
        return f"Transkript vom {datetime.datetime.now().strftime('%d.%m.%Y')}"

