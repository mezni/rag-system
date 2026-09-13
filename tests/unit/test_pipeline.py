from pathlib import Path

from src.ingestion.pipeline import diff_against_store, normalize_source_id
from src.ingestion.stages.parse import DiscoveredFile


def _disc(path: Path, content_hash: str) -> DiscoveredFile:
    return DiscoveredFile(path=path, content_hash=content_hash, mtime=0.0)


class _FakeStore:
    """Minimal stand-in for ``PostgreSQLStateStore.get_active_documents``."""

    def __init__(self, active: dict[str, str]):
        self._active = [
            {
                "id": f"id-{sid}",
                "source_id": sid,
                "content_hash": content_hash,
                "is_active": True,
            }
            for sid, content_hash in active.items()
        ]

    def get_active_documents(self):
        return list(self._active)


def test_normalize_source_id_relative_to_scan_root():
    root = Path("/srv/data/raw")
    assert normalize_source_id(root / "billing/a.pdf", root) == "billing/a.pdf"


def test_normalize_source_id_via_mount_anchor():
    scan_root = Path("/srv/data/raw")
    path = Path("/rag-system/data/raw/billing/a.pdf")
    anchor = Path("/rag-system/data/raw")
    assert normalize_source_id(path, scan_root, mount_anchor=anchor) == "billing/a.pdf"


def test_normalize_source_id_foreign_absolute_fallback():
    scan_root = Path("/srv/data/raw")
    path = Path("/app/data/raw/billing/a.pdf")
    assert normalize_source_id(path, scan_root) == "billing/a.pdf"


def test_normalize_source_id_raw_path_last_resort():
    scan_root = Path("/srv/data/raw")
    path = Path("/somewhere/else/standalone.txt")
    assert normalize_source_id(path, scan_root) == "/somewhere/else/standalone.txt"


def test_diff_classifies_new_modified_unchanged_deleted():
    root = Path("/tmp/srcdir")
    discovered = [
        _disc(root / "new.md", "hA"),
        _disc(root / "mod.md", "hB2"),
        _disc(root / "same.md", "hC"),
    ]
    store = _FakeStore(
        {
            "mod.md": "hB1",
            "same.md": "hC",
            "gone.md": "hD",
        }
    )

    diff = diff_against_store(store, discovered, source_dir=root)

    assert {d.path.name for d in diff["new"]} == {"new.md"}
    assert {d.path.name for d in diff["modified"]} == {"mod.md"}
    assert {d.path.name for d in diff["unchanged"]} == {"same.md"}
    assert diff["deleted"] == [{"id": "id-gone.md", "source_id": "gone.md"}]


def test_diff_never_maps_unchanged_to_modified():
    root = Path("/tmp/srcdir")
    discovered = [_disc(root / "same.md", "hC")]
    store = _FakeStore({"same.md": "hC"})

    diff = diff_against_store(store, discovered, source_dir=root)

    assert diff["modified"] == []
    assert diff["new"] == []
    assert len(diff["unchanged"]) == 1