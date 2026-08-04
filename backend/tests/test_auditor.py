import asyncio
from playwright.async_api import Error as PlaywrightError

from app import auditor
from app.auditor import _body_word_count, check_javascript, extract_schema


def test_body_word_count_ignores_head():
    assert _body_word_count("<head><title>ignore me</title></head><body>Count these three</body>") == 3


def test_extract_schema_finds_nested_types_and_invalid_scripts():
    html = '''
      <script type="application/ld+json">{"@graph":[{"@type":"Organization"},{"@type":["WebSite", "Thing"]}]}</script>
      <script type="application/ld+json">not json</script>
    '''
    report = extract_schema(html)
    assert report.script_count == 2
    assert report.invalid_script_count == 1
    assert report.key_entities["Organization"] is True
    assert report.key_entities["Article"] is False


def test_javascript_check_reports_unavailable_browser(monkeypatch):
    async def unavailable_browser(url: str) -> str:
        raise PlaywrightError("Executable doesn't exist")

    monkeypatch.setattr(auditor, "render_html", unavailable_browser)

    report = asyncio.run(check_javascript("https://example.com", "<body>Raw content</body>"))

    assert report.rendering_available is False
    assert report.error == (
        "Browser rendering is unavailable in this deployment; "
        "JavaScript reliance could not be evaluated."
    )
    assert report.raw_word_count == 2
    assert report.rendered_word_count is None
    assert report.raw_to_rendered_ratio is None
    assert report.js_reliant is None


def test_javascript_check_compares_rendered_content(monkeypatch):
    async def rendered_page(url: str) -> str:
        return "<body>one two three four five six</body>"

    monkeypatch.setattr(auditor, "render_html", rendered_page)

    report = asyncio.run(check_javascript("https://example.com", "<body>one</body>"))

    assert report.rendering_available is True
    assert report.error is None
    assert report.raw_to_rendered_ratio == 0.167
    assert report.js_reliant is True
