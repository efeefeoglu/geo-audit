from app.auditor import _body_word_count, extract_schema


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
