CREATE TABLE ingestion_runs (
    run_id UUID PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error TEXT
);

CREATE INDEX idx_ingestion_runs_document_id
    ON ingestion_runs(document_id);

CREATE INDEX idx_ingestion_runs_status
    ON ingestion_runs(status);