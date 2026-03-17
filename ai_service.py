import os
from groq import Groq
from dotenv import load_dotenv

# Setup
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(uploaded_file):
    """Schritt 1: Audio zu Text umwandeln (Whisper)"""
    file_content = uploaded_file.read()
    transcription = client.audio.transcriptions.create(
        file=(uploaded_file.name, file_content),
        model="whisper-large-v3",
        response_format="json"
    )
    return transcription.text

def process_with_ai_action(uploaded_file, action):
    """Schritt 2: Den Text basierend auf der Auswahl verarbeiten"""
    raw_text = transcribe_audio(uploaded_file)

    if action == "Transkribieren":
        return raw_text

    if action == "Zusammenfassen":
        system_prompt = "Fasse den folgenden Text kurz und prägnant zusammen."
    elif action == "Wichtige Punkte extrahieren":
        system_prompt = "Extrahiere die wichtigsten Kernpunkte aus dem Text als Bulletpoints."
    else:
        return raw_text

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        temperature=0.5
    )
    return completion.choices[0].message.content