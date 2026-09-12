-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create rag user and database
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rag_user') THEN
        CREATE USER rag_user WITH PASSWORD 'rag_password';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rag_ingestion') THEN
        CREATE DATABASE rag_ingestion OWNER rag_user;
    END IF;
    
    GRANT ALL PRIVILEGES ON DATABASE rag_ingestion TO rag_user;
    GRANT ALL PRIVILEGES ON SCHEMA public TO rag_user;
END
$$;