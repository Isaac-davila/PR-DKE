import os
import warnings

import torch
import torchaudio
from pyannote.audio import Pipeline
from dotenv import load_dotenv

load_dotenv()


def load_pipeline() -> Pipeline:
    """
    Loads the pyannote speaker diarization pipeline.

    Requires HF_TOKEN to be set in .env (Hugging Face access token).
    Uses CUDA if available, falls back to CPU with a performance warning.
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise EnvironmentError("HF_TOKEN environment variable is not set.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cpu":
        warnings.warn(
            "No GPU detected — diarization runs on CPU. "
            "Expect several minutes for longer audio files.",
            RuntimeWarning,
            stacklevel=2,
        )

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    pipeline.to(device)
    return pipeline


def load_audio(audio_path: str) -> dict:
    """
    Loads and pre-processes audio for pyannote:
    - Resamples to 16 kHz if needed
    - Converts to mono if needed

    Returns a dict with 'waveform' and 'sample_rate' keys.
    """
    waveform, sample_rate = torchaudio.load(audio_path)

    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(
            orig_freq=sample_rate, new_freq=16000
        )
        waveform = resampler(waveform)

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    return {"waveform": waveform, "sample_rate": 16000}


def diarize(audio_path: str) -> list[dict]:
    """
    Runs speaker diarization on a local audio file.

    Args:
        audio_path: Absolute path to the audio file (mp3, wav, etc.).

    Returns:
        List of segment dicts with keys: speaker, start, end, text.
        'text' is always empty here — it is filled in by the caller.

    Raises:
        FileNotFoundError: If audio_path does not exist.
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    pipeline = load_pipeline()
    audio_input = load_audio(audio_path)
    diarization_result = pipeline(audio_input)

    segments = []
    for segment, _, speaker in diarization_result.itertracks(yield_label=True):
        segments.append({
            "speaker": speaker,
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": "",
        })

    return segments