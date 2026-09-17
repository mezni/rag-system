def test_record_success(database_session):
    from src.services.ingestion_run_service import (
        IngestionRunService,
    )
    from src.services.document_processing_service import (
        DocumentProcessingService,
    )

    run_service = IngestionRunService(database_session)
    processing_service = DocumentProcessingService(
        database_session
    )

    run = run_service.start("ingestion")

    record = processing_service.record_success(
        run_id=run.id,
        source_uri="data/raw/test.md",
        operation="add",
    )

    database_session.commit()

    assert record.id is not None
    assert record.run_id == run.id
    assert record.status == "success"