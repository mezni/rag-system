from src.domain.ingestion_run import (
    IngestionRun,
    IngestionStatus,
)


def test_create_run() -> None:
    run = IngestionRun.create(
        document_id="/documents/policy.txt"
    )

    assert run.document_id == "/documents/policy.txt"
    assert run.status == IngestionStatus.PENDING
    assert run.started_at is None
    assert run.completed_at is None
    assert run.error is None
    assert run.run_id is not None


def test_start_run() -> None:
    run = IngestionRun.create(
        document_id="/documents/policy.txt"
    )

    run.start()

    assert run.status == IngestionStatus.RUNNING
    assert run.started_at is not None
    assert run.completed_at is None


def test_succeed_run() -> None:
    run = IngestionRun.create(
        document_id="/documents/policy.txt"
    )

    run.start()
    run.succeed()

    assert run.status == IngestionStatus.SUCCEEDED
    assert run.started_at is not None
    assert run.completed_at is not None
    assert run.error is None


def test_fail_run() -> None:
    run = IngestionRun.create(
        document_id="/documents/policy.txt"
    )

    run.start()
    run.fail("Embedding service unavailable")

    assert run.status == IngestionStatus.FAILED
    assert run.started_at is not None
    assert run.completed_at is not None
    assert run.error == "Embedding service unavailable"