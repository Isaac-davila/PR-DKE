from download_service import DownloadService


def test_sanitize_filename():
    result = DownloadService.sanitize_filename("My File!.mp3")
    assert result == "my_filemp3"


def test_create_txt():
    markdown = "# Titel\n## Untertitel\n---\nText"
    result = DownloadService.create_txt(markdown)

    assert "# " not in result
    assert "## " not in result
    assert "---" not in result
    assert "Titel" in result


def test_build_filename():
    result = DownloadService.build_filename(
        "2026-06-08",
        "summary",
        "audiofile",
        "txt"
    )

    assert result == "2026-06-08_summary_audiofile.txt"


def test_generate_markdown_file():
    data, filename, mime = DownloadService.generate_file(
        markdown_content="# Test",
        format_choice="Markdown (.md)",
        filename="audio",
        prefix="summary",
        title="Test"
    )

    assert "# Test" in data
    assert filename.endswith(".md")
    assert mime == "text/markdown"


def test_generate_txt_file():
    data, filename, mime = DownloadService.generate_file(
        markdown_content="# Test",
        format_choice="Text (.txt)",
        filename="audio",
        prefix="summary",
        title="Test"
    )

    assert "Test" in data
    assert filename.endswith(".txt")
    assert mime == "text/plain"