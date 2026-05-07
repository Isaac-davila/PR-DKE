import os
import tempfile
from dotenv import load_dotenv

from ai_service import transcribe_audio
from diarize import diarize

load_dotenv()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_segments_as_text(segments: list[dict]) -> str:
    """
    Converts a list of diarization segments into a readable transcript string.
    Each line shows: [SPEAKER @ start_time] text
    """
    lines = []
    for seg in segments:
        speaker = seg.get("speaker", "?")
        text = seg.get("text", "").strip()
        start = seg.get("start", 0)
        if text:
            lines.append(f"[{speaker} @ {start:.1f}s] {text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pipeline implementations
# ---------------------------------------------------------------------------

def _run_groq_only(uploaded_file) -> str:
    """
    Cloud-only path: Groq Whisper transcription, no diarization.
    Fast and cheap — good default for single-speaker audio.
    """
    return transcribe_audio(uploaded_file)


def _run_groq_local(uploaded_file) -> str:
    """
    Groq transcription + local pyannote diarization (CPU-fallback).

    Because pyannote needs a file path rather than a file object,
    the upload is written to a temp file first. The full Groq transcript
    is then naively assigned to the first segment.

    TODO: Replace naive assignment with proper word-level timestamp matching
          once Groq Whisper exposes word-level timestamps.
    """
    # Write to disk so pyannote can open it by path
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Reset so Groq can read the file again
    uploaded_file.seek(0)

    try:
        segments = diarize(tmp_path)
        full_transcript = transcribe_audio(uploaded_file)

        # Naive assignment — all text goes to the first speaker segment
        if segments:
            segments[0]["text"] = full_transcript

        return _format_segments_as_text(segments)
    finally:
        os.unlink(tmp_path)


def _run_assemblyai(uploaded_file) -> str:
    """
    AssemblyAI path — transcription + speaker diarization in a single API call.
    Slower than Groq but produces accurate per-speaker segments.
    """
    import assemblyai as aai

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        raise ValueError("ASSEMBLYAI_API_KEY is not set in .env")

    aai.settings.api_key = api_key

    # speech_model must be a SpeechModel enum value, not a list
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speech_model=aai.SpeechModel.best,
    )

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(uploaded_file, config=config)

    if not transcript.utterances:
        # Fallback: return plain text if diarization produced no utterances
        return transcript.text or ""

    # Normalise AssemblyAI utterances into our segment format
    # (AssemblyAI timestamps are in milliseconds)
    segments = [
        {
            "speaker": f"SPEAKER_{utt.speaker}",
            "start": round(utt.start / 1000, 3),
            "end": round(utt.end / 1000, 3),
            "text": utt.text,
        }
        for utt in transcript.utterances
    ]
    return _format_segments_as_text(segments)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(uploaded_file, mode: str) -> str:
    """
    Routes an audio file through the selected transcription pipeline.

    Args:
        uploaded_file: Streamlit UploadedFile object.
        mode:          "groq" | "groq_local" | "assemblyai"

    Returns:
        Formatted transcript string, ready to display and save.

    Raises:
        ValueError: If an unknown mode is provided.
    """
    if mode == "groq":
        return _run_groq_only(uploaded_file)
    elif mode == "groq_local":
        return _run_groq_local(uploaded_file)
    elif mode == "assemblyai":
        return _run_assemblyai(uploaded_file)
    else:
        raise ValueError(f"Unknown pipeline mode: '{mode}'")