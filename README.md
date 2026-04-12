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

## Addendum zur Installation:
[requirements.txt](requirements.txt) erstellt - hier sind alle Abhängigkeiten drin. Bei manueller Installation kracht es sehr oft, daher empfehle ich im Projekt Python 3.11 zu verwenden und die benötigten Plugins über requirements.txt zu holen:

`py -3.11 -m venv .venv`  
`.\.venv\Scripts\pip.exe install -r requirements.txt`

Start wie oben oder noch besser so:  
`.\.venv\Scripts\streamlit.exe run app.py`

## Team
- Jason
- Adem
- Paul
- Elias
- Isaac Davila Mendez
