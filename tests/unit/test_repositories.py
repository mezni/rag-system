from uuid import UUID, uuid4

from src.domain.ingestion_run import IngestionRun, IngestionStatus
from src.domain.repositories import IngestionRunRepository


class InMemoryIngestionRunRepository:
    """In-memory implementation of IngestionRunRepository."""

    def __init__(self) -> None:
        self._runs: dict[UUID, IngestionRun] = {}

    def save(self, run: IngestionRun) -> None:
        self._runs[run.run_id] = run

    def get(self, run_id: UUID) -> IngestionRun | None:
        return self._runs.get(run_id)


def _in_memory_repo() -> InMemoryIngestionRunRepository:
    return InMemoryIngestionRunRepository()


def test_repo_implements_protocol() -> None:
    repo: IngestionRunRepository = _in_memory_repo()

    assert repo is not None


def test_save_and_get_roundtrip() -> None:
    repo = _in_memory_repo()

    run = IngestionRun.create(document_id="policy.txt")
    run.start()
    run.succeed()

    repo.save(run)

    restored = repo.get(run.run_id)

    assert restored is not None
    assert restored.run_id == run.run_id
    assert restored.document_id == "policy.txt"
    assert restored.status == IngestionStatus.SUCCEEDED
    assert restored.started_at is not None
    assert restored.completed_at is not None
    assert restored.error is None


def test_get_missing_run_returns_none() -> None:
    repo = _in_memory_repo()

    assert repo.get(uuid4()) is None


def test_repo_preserves_failed_run() -> None:
    repo = _in_memory_repo()

    run = IngestionRun.create(document_id="roaming.pdf")
    run.start()
    run.fail("Embedding service unavailable")

    repo.save(run)

    restored = repo.get(run.run_id)

    assert restored is not None
    assert restored.status == IngestionStatus.FAILED
    assert restored.error == "Embedding service unavailable"


def test_repo_overwrites_same_run_id() -> None:
    repo = _in_memory_repo()

    run_id = uuid4()
    first = IngestionRun(
        run_id=run_id,
        document_id="policy.txt",
        status=IngestionStatus.PENDING,
    )
    second = IngestionRun(
        run_id=run_id,
        document_id="policy.txt",
        status=IngestionStatus.SUCCEEDED,
    )

    repo.save(first)
    repo.save(second)

    restored = repo.get(run_id)

    assert restored is not None
    assert restored.status == IngestionStatus.SUCCEEDED