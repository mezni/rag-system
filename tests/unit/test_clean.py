from src.ingestion.stages.clean import clean_text


def test_collapses_inline_whitespace():
    assert clean_text("a   b\tc  d") == "a b c d"


def test_collapses_runs_of_newlines():
    assert clean_text("one\n\n\n\ntwo") == "one\n\ntwo"


def test_strips_leading_and_trailing_whitespace():
    assert clean_text("  hello  \n  ") == "hello"


def test_preserves_single_paragraph_breaks():
    assert clean_text("one\n\ntwo") == "one\n\ntwo"


def test_idempotent():
    text = "a   b\n\n\n\nc"
    assert clean_text(clean_text(text)) == clean_text(text)