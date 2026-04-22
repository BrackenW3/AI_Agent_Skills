-- Vector search indexing pipeline - Supabase schema setup
-- Run this SQL in your Supabase SQL editor to set up the required tables and functions

-- Enable vector extension (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table: stores chunks with embeddings
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    file_hash TEXT NOT NULL,
    file_source TEXT NOT NULL, -- 'onedrive', 'google_drive', 'local'
    file_path TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE(file_hash, chunk_index)
);

-- Metadata table: tracks file processing and deduplication
CREATE TABLE IF NOT EXISTS file_metadata (
    id BIGSERIAL PRIMARY KEY,
    file_hash TEXT UNIQUE NOT NULL,
    file_path TEXT NOT NULL,
    file_source TEXT NOT NULL, -- 'onedrive', 'google_drive', 'local'
    file_size_bytes INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    last_modified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    status TEXT DEFAULT 'active', -- 'active', 'archived', 'deleted'
    metadata JSONB, -- additional metadata as JSON
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Similarity search function
-- Usage: SELECT * FROM match_documents(embedding, 0.7, 10)
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
) RETURNS TABLE (
    id BIGINT,
    file_path TEXT,
    file_source TEXT,
    chunk_text TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.file_path,
        documents.file_source,
        documents.chunk_text,
        (1 - (documents.embedding <=> query_embedding))::FLOAT AS similarity
    FROM documents
    WHERE (1 - (documents.embedding <=> query_embedding)) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_file_source ON documents(file_source);
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding VECTOR_COSINE_OPS) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_file_metadata_file_hash ON file_metadata(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_source ON file_metadata(file_source);
CREATE INDEX IF NOT EXISTS idx_file_metadata_status ON file_metadata(status);

-- Grant permissions (adjust to your Supabase role)
GRANT ALL ON documents TO anon;
GRANT ALL ON documents TO authenticated;
GRANT ALL ON file_metadata TO anon;
GRANT ALL ON file_metadata TO authenticated;
GRANT EXECUTE ON FUNCTION match_documents TO anon;
GRANT EXECUTE ON FUNCTION match_documents TO authenticated;
