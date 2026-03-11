# DKE Audio-to-Text Agent 🎙️

Dieses Projekt ist Teil des Praktikums "Data & Knowledge Engineering" (PR). 
Der Agent ermöglicht den Upload von MP3-Dateien und transkribiert diese mithilfe der Groq-API (Whisper-Modell).

## Features
- MP3 Audio Upload via Streamlit Interface
- Schnelle Transkription via Groq Cloud
- Preview-Player für Audio-Files

## Installation & Start
1. Repository klonen:
   `git clone https://github.com/Isaac-davila/PR-DKE.git`
2. Virtuelle Umgebung erstellen und aktivieren:
   `python -m venv .venv`
3. Benötigte Pakete installieren:
   `pip install streamlit groq python-dotenv`
4. `.env` Datei im Hauptverzeichnis erstellen und API Key hinzufügen:
   `GROQ_API_KEY=dein_key_hier`
5. App starten:
   `streamlit run app.py`

## Team
- Isaac
- Jason
- Adem
- Paul
- Elias
