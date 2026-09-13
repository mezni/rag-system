from src.ingestion.stages.persist import _filter_fields


def test_filter_fields_extraction():
    lineage = {
        "tenant_id": "t1",
        "access_roles": ["billing_admin", "support_tier_2"],
        "category": "billing",
        "department": "billing",
        "classification": "internal",
        "language": "en",
        "header_path": "Billing > Refunds",
        "chunk_kind": "section",
    }

    assert _filter_fields(lineage) == {
        "tenant_id": "t1",
        "access_roles": ["billing_admin", "support_tier_2"],
        "category": "billing",
        "department": "billing",
        "classification": "internal",
        "language": "en",
    }


def test_filter_fields_none():
    assert _filter_fields(None) == {
        "tenant_id": None,
        "access_roles": None,
        "category": None,
        "department": None,
        "classification": None,
        "language": None,
    }


def test_filter_fields_ignores_hierarchy_only_tags():
    lineage = {"header_path": "A > B", "sections": ["A"], "chunk_kind": "table"}
    output = _filter_fields(lineage)
    assert "header_path" not in output
    assert "sections" not in output
    assert "chunk_kind" not in output