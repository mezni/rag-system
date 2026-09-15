from src.infrastructure.change_detection.json_tracker import JsonChangeTracker


def test_get_hash_missing_returns_none(tmp_path) -> None:
    tracker = JsonChangeTracker(tmp_path / "state.json")

    assert tracker.get_hash("f1") is None


def test_set_and_get_hash(tmp_path) -> None:
    tracker = JsonChangeTracker(tmp_path / "state.json")

    tracker.set_hash("f1", "abc")
    tracker.set_hash("f2", "def")

    assert tracker.get_hash("f1") == "abc"
    assert tracker.get_hash("f2") == "def"


def test_hashes_persist_across_instances(tmp_path) -> None:
    path = tmp_path / "nested" / "state.json"
    JsonChangeTracker(path).set_hash("f1", "abc")

    reloaded = JsonChangeTracker(path)

    assert reloaded.get_hash("f1") == "abc"