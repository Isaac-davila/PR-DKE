import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(uploaded_file):
    file_content = uploaded_file.read()
    transcription = client.audio.transcriptions.create(
        file=(uploaded_file.name, file_content),
        model="whisper-large-v3",
        response_format="json"
    )
    return transcription.text

def process_with_ai_action(uploaded_file, action, available_tags=None):
    raw_text = transcribe_audio(uploaded_file)
    if action == "Transkribieren": return raw_text, []

    # TODO:
    # Expand prompts to provide better output quality. Keep diarization and the pipeline in mind
    prompts = {"Zusammenfassen": "Fasse kurz zusammen.", "Wichtige Punkte extrahieren": "Extrahiere Kernpunkte."}
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": prompts.get(action, "")},
                  {"role": "user", "content": raw_text}]
    )
    return completion.choices[0].message.content, []