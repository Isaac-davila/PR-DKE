import os
import torch
import warnings

import torchaudio
from pyannote.audio import Pipeline
from dotenv import load_dotenv

load_dotenv()

def load_pipeline() -> Pipeline:
    hf_token = os.getenv("HF_TOKEN")
    if hf_token is None:
        raise Exception("HF_TOKEN environment variable not set")

    # Important for performance: If you have a CUDA-capable card, it should use that.
    # For testing purposes, torchaudio is set to use only CPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cpu":
        warnings.warn(
            "No GPU detected — diarization runs on CPU. "
            "Expect several minutes for longer audio files.",
            RuntimeWarning
        )

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )
    pipeline.to(device)
    return pipeline


def load_audio(audio_path: str) -> dict:
    waveform, sample_rate = torchaudio.load(audio_path)

    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform = resampler(waveform)

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    return {"waveform": waveform, "sample_rate": 16000}


def diarize(audio_path: str) -> list[dict]:
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    pipeline = load_pipeline()
    audio_input = load_audio(audio_path)
    diarization = pipeline(audio_input).speaker_diarization

    segments = []
    count = 0;
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        print(f"count {count}")
        count += 1
        segments.append({
            "speaker": speaker,
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": ""
        })

    return segments