import hashlib

from src.ingestion.stages import chunk as ch
from src.ingestion.stages.parse import ParsedContent


def _block(text, header="", page=None, kind="section", start=0):
    return {
        "text": text,
        "char_start": start,
        "char_end": start + len(text) - 1,
        "header_path": header,
        "page": page,
        "kind": kind,
    }


def test_token_budget_converts_chars_to_tokens():
    assert ch._token_budget(1500, 200) == (375, 50)
    assert ch._token_budget(100, 1000) == (32, 16)  # floors/ceilings


def test_legacy_chunk_text_short_document():
    assert ch.chunk_text("hello world", 1500, 200) == ["hello world"]


def test_legacy_chunk_text_splits_at_paragraph_boundary():
    text = ("word " * 400) + "\n\n" + ("tail " * 400)
    parts = ch.chunk_text(text, 800, 100)
    assert len(parts) >= 2
    assert all(p.strip() for p in parts)


def test_fixed_strategy_matches_legacy():
    parsed = ParsedContent(text="a" * 2200, lineage=[{"char_start": 0}])
    records = ch.build_chunk_records(parsed, 1000, 200, strategy="fixed")
    assert len(records) > 1
    assert records[0].chunk_index == 0
    for r in records:
        expected_hash = hashlib.sha256(r.content.encode("utf-8")).hexdigest()
        assert r.content_hash == expected_hash


def test_semantic_grouping_respects_section_boundaries():
    blocks = [
        _block("A" * 700, header="Intro"),
        _block("B" * 700, header="Intro"),
        _block("C" * 700, header="Audit"),
        _block("D" * 700, header="Refunds"),
    ]
    parsed = ParsedContent(text="", blocks=blocks)
    records = ch.build_chunk_records(parsed, 1500, 200, strategy="semantic")

    assert len(records) == 2
    assert records[0].lineage["header_path"] == "Intro"
    assert records[0].lineage["source_blocks"] == 2
    assert records[1].lineage["source_blocks"] == 2
    assert records[1].lineage["header_path"] == "Refunds"  # deepest of [Audit, Refunds]
    assert records[1].lineage["chunk_kind"] == "section"
    assert records[0].lineage["char_start"] == 0


def test_oversized_block_is_recursively_split_and_keeps_header():
    blocks = [
        _block(
            "Sentence one about roaming rates in portugal. " * 60,
            header="Roaming > Portugal",
            page=2,
        )
    ]
    parsed = ParsedContent(text="", blocks=blocks)
    records = ch.build_chunk_records(parsed, 400, 50, strategy="semantic")

    assert len(records) > 1
    assert all(r.lineage["header_path"] == "Roaming > Portugal" for r in records)
    assert all(r.lineage["page_start"] == r.lineage["page_end"] == 2 for r in records)
    assert "roaming" in records[0].content.lower()


def test_oversized_split_falls_back_when_tokenizer_unavailable(monkeypatch):
    class BoomSplitter:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("tokenizer unavailable")

    monkeypatch.setattr(ch, "SentenceSplitter", BoomSplitter)
    blocks = [_block("x" * 3000, header="H")]
    parsed = ParsedContent(text="", blocks=blocks)
    records = ch.build_chunk_records(parsed, 500, 50, strategy="semantic")

    assert records
    assert all(r.lineage["header_path"] == "H" for r in records)


def test_table_blocks_are_atomic_chunk_kind():
    blocks = [
        _block("country: portugal, rate: 0.45", header="", kind="table"),
        _block("country: spain, rate: 0.40", header="", kind="table"),
    ]
    parsed = ParsedContent(text="", blocks=blocks)
    records = ch.build_chunk_records(parsed, 1500, 200, strategy="semantic")

    assert len(records) == 1
    assert records[0].lineage["chunk_kind"] == "table"
    assert "spain" in records[0].content


def test_empty_input_returns_no_records():
    assert ch.build_chunk_records(ParsedContent(text="", blocks=[]), 1000, 100) == []
    assert ch.build_chunk_records(ParsedContent(text="   ", blocks=[]), 1000, 100) == []