from ai_service import process_with_ai_action, generate_title
from unittest.mock import patch


def test_process_transcription_action():
    result, tags = process_with_ai_action(
        "Hallo Welt",
        "Transkribieren"
    )

    assert result == "Hallo Welt"
    assert tags == []


@patch("ai_service.client.chat.completions.create")
def test_generate_title_fallback(mock_create):
    mock_create.side_effect = Exception("API down")

    result = generate_title("Hallo")

    assert "Transkript vom" in result