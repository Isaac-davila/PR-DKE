from pipeline import (
    extract_speakers,
    apply_speaker_mapping,
    _format_segments_as_text,
    run_pipeline
)

from unittest.mock import patch


def test_extract_speakers():
    transcript = """
    [SPEAKER_1 @ 0.0s] Hallo
    [SPEAKER_2 @ 5.0s] Hi
    [SPEAKER_1 @ 8.0s] Wieder da
    """

    result = extract_speakers(transcript)

    assert result == ["SPEAKER_1", "SPEAKER_2"]


def test_apply_speaker_mapping():
    transcript = "[SPEAKER_1 @ 0.0s] Hallo"

    mapping = {
        "SPEAKER_1": "Max"
    }

    result = apply_speaker_mapping(transcript, mapping)

    assert "[Max @" in result


def test_format_segments_as_text():
    segments = [
        {
            "speaker": "SPEAKER_1",
            "start": 0.0,
            "text": "Hallo"
        },
        {
            "speaker": "SPEAKER_2",
            "start": 5.2,
            "text": "Hi"
        }
    ]

    result = _format_segments_as_text(segments)

    assert "[SPEAKER_1 @ 0.0s] Hallo" in result
    assert "[SPEAKER_2 @ 5.2s] Hi" in result


@patch("pipeline._run_groq_only")
def test_run_pipeline_groq(mock_run):
    mock_run.return_value = "transcript"

    result = run_pipeline("fakefile", "groq")

    assert result == "transcript"
    mock_run.assert_called_once()


def test_invalid_pipeline_mode():
    try:
        run_pipeline("fake", "invalid_mode")
    except ValueError as e:
        assert "Unknown pipeline mode" in str(e)
