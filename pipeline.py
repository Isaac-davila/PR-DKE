import os
import tempfile

from assemblyai import SpeechModel
from dotenv import load_dotenv
from ai_service import transcribe_audio, process_with_ai_action
from diarize import diarize

load_dotenv()


def _format_segments_as_text(segments: list[dict]) -> str:
    """
    Converts a list of segments into a readable transcript string.
    Used when diarization is active — each line shows speaker + text.
    """
    lines = []
    for seg in segments:
        speaker = seg.get("speaker", "?")
        text = seg.get("text", "").strip()
        start = seg.get("start", 0)
        if text:
            lines.append(f"[{speaker} @ {start:.1f}s] {text}")
    return "\n".join(lines)


def _run_groq_only(uploaded_file) -> str:
    transcript = transcribe_audio(uploaded_file)
    return transcript



def _run_groq_local(uploaded_file, action: str) -> str:
    """
    Groq transcription + local pyannote diarization.

    Because pyannote needs a file path (not a file object),
    we write the uploaded file to a temp file first, run diarization
    to get speaker segments with timestamps, then use Groq Whisper
    to transcribe and assign text to each segment by matching timestamps.
    """
    # Write uploaded file to disk temporarily
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    uploaded_file.seek(0)  # Reset so Groq can read it again

    try:
        # Step 1: Get speaker segments (text is empty at this point)
        segments = diarize(tmp_path)

        # Step 2: Get full transcript from Groq
        full_transcript = transcribe_audio(uploaded_file)

        # Step 3: Naively assign the full transcript to the first segment
        # TODO: proper word-level timestamp matching when Groq supports it
        if segments:
            segments[0]["text"] = full_transcript

        formatted =  _format_segments_as_text(segments)
        return formatted
    finally:
        os.unlink(tmp_path)  # Always clean up the temp file


def _run_assemblyai(uploaded_file) -> str:
    """
    AssemblyAI path — handles transcription + diarization in one API call.
    Returns speaker-labeled segments, then optionally runs Groq LLM on them.
    """
    import assemblyai as aai
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not aai.settings.api_key:
        raise ValueError("ASSEMBLYAI_API_KEY not found in .env file.")

    config = aai.TranscriptionConfig(speaker_labels=True, speech_models=["universal-2"]) #fuck this
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(uploaded_file, config=config)

    # Normalize AssemblyAI output into our segment format
    segments = [
        {
            "speaker": f"SPEAKER_{utt.speaker}",
            "start": round(utt.start / 1000, 3),  # AssemblyAI uses milliseconds
            "end": round(utt.end / 1000, 3),
            "text": utt.text
        }
        for utt in transcript.utterances
    ]
    formatted = _format_segments_as_text(segments)
    return formatted


def run_pipeline(uploaded_file, mode: str) -> str:
    """
    Main entry point. Routes to the correct pipeline based on mode.

    Args:
        uploaded_file: Streamlit UploadedFile object
        action:        "Transkribieren" | "Zusammenfassen" | "Wichtige Punkte extrahieren"
        mode:          "groq" | "groq_local" | "assemblyai"

    Returns:
        Formatted string result ready to display and save.
    """
    if mode == "groq":
        return _run_groq_only(uploaded_file)
    elif mode == "groq_local":
        return _run_groq_local(uploaded_file)
    elif mode == "assemblyai":
        return _run_assemblyai(uploaded_file)
    else:
        raise ValueError(f"Unknown pipeline mode: {mode}")