-- Database initialization script for Legal Ingest
-- Creates tables for documents, metadata, and versioning

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,  -- SHA-256 hash
    source VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,  -- Full text content
    content_hash VARCHAR(64) NOT NULL,
    language VARCHAR(10) NOT NULL,
    category VARCHAR(50),
    document_type VARCHAR(50),
    jurisdiction VARCHAR(100),
    metadata JSONB,
    scraped_at TIMESTAMP,
    normalized_at TIMESTAMP NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for documents
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_documents_language ON documents(language);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN (metadata);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_documents_title_fts ON documents USING GIN (to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_content_fts ON documents USING GIN (to_tsvector('english', content));

-- Document versions table (for tracking changes)
CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    diff JSONB,  -- Stores diff information
    UNIQUE(document_id, version)
);

CREATE INDEX IF NOT EXISTS idx_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_versions_changed_at ON document_versions(changed_at);

-- Sources configuration table
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    url TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 3,
    languages TEXT[],
    frequency VARCHAR(50),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_scraped TIMESTAMP,
    config JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_enabled ON sources(enabled);
CREATE INDEX IF NOT EXISTS idx_sources_priority ON sources(priority);

-- Scraping jobs table (for tracking ingestion runs)
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    source_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, running, completed, failed
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    documents_found INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_jobs_source_id ON scraping_jobs(source_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON scraping_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_started_at ON scraping_jobs(started_at);

-- Sync status table (for PlanetHoster sync)
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_sync TIMESTAMP,
    last_sync_documents INTEGER DEFAULT 0,
    last_sync_status VARCHAR(50),
    CHECK (id = 1)  -- Only one row allowed
);

-- Insert default sync status
INSERT INTO sync_status (id, last_sync, last_sync_status)
VALUES (1, '2000-01-01'::TIMESTAMP, 'never')
ON CONFLICT (id) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create user for read-only access (PlanetHoster cache)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'legal_cache_ro') THEN
        CREATE ROLE legal_cache_ro WITH LOGIN PASSWORD 'changeme';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE legal_data TO legal_cache_ro;
GRANT USAGE ON SCHEMA public TO legal_cache_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO legal_cache_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO legal_cache_ro;

-- Grant permissions to main user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO legal_ingest;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO legal_ingest;

-- Statistics for query optimization
ANALYZE documents;
ANALYZE document_versions;
ANALYZE sources;
ANALYZE scraping_jobs;
