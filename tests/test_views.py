from views.views import format_transcript


def test_format_transcript():
    text = """
    [Teacher @ 10.2s] Good morning.
    [Student @ 12.0s] Hello.
    """

    result = format_transcript(text)

    assert "**Teacher:** Good morning." in result
    assert "**Student:** Hello." in result


def test_format_transcript_without_speakers():
    text = "Normal transcript"

    result = format_transcript(text)

    assert result == text