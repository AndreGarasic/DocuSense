-- DocuSense Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64),
    content_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create document_chunks table with vector column
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384),  -- Dimension for all-MiniLM-L6-v2
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);

-- Create vector index for similarity search (using IVFFlat for better performance)
-- Note: This index is created after data is inserted for better accuracy
-- For now, we create a basic index
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Grant permissions (if needed for specific users)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO docusense;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO docusense;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'DocuSense database initialized successfully with pgvector extension';
END $$;
