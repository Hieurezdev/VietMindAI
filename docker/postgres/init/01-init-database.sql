-- Initialize vietmindai-ADK Database with pgvectorscale
-- This script runs automatically when the container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Install vector extensions (pgvector is a dependency for pgvectorscale)
CREATE EXTENSION IF NOT EXISTS vector;

-- Install pgvectorscale for high-performance vector operations
CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;

-- Create schemas for organization
CREATE SCHEMA IF NOT EXISTS ai_data;
CREATE SCHEMA IF NOT EXISTS embeddings;
CREATE SCHEMA IF NOT EXISTS agents;

-- Grant permissions to the application user
GRANT USAGE ON SCHEMA ai_data TO mindai_user;
GRANT USAGE ON SCHEMA embeddings TO mindai_user;
GRANT USAGE ON SCHEMA agents TO mindai_user;

GRANT CREATE ON SCHEMA ai_data TO mindai_user;
GRANT CREATE ON SCHEMA embeddings TO mindai_user;
GRANT CREATE ON SCHEMA agents TO mindai_user;

-- Example table for storing embeddings with pgvectorscale
CREATE TABLE IF NOT EXISTS embeddings.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002 embedding dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vectorscale index for high-performance similarity search
-- This uses StreamingDiskANN for better performance than standard HNSW
CREATE INDEX IF NOT EXISTS documents_embedding_idx 
ON embeddings.documents 
USING diskann (embedding vector_cosine_ops);

-- Grant permissions on the table
GRANT ALL PRIVILEGES ON TABLE embeddings.documents TO mindai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA embeddings TO mindai_user;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for auto-updating timestamps
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON embeddings.documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Example table for agent conversations
CREATE TABLE IF NOT EXISTS agents.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    user_message TEXT,
    agent_response TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster conversation lookups
CREATE INDEX IF NOT EXISTS conversations_session_id_idx ON agents.conversations(session_id);
CREATE INDEX IF NOT EXISTS conversations_agent_type_idx ON agents.conversations(agent_type);
CREATE INDEX IF NOT EXISTS conversations_created_at_idx ON agents.conversations(created_at);

-- Grant permissions
GRANT ALL PRIVILEGES ON TABLE agents.conversations TO mindai_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agents TO mindai_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'vietmindai-ADK database initialized successfully with pgvectorscale!';
    RAISE NOTICE 'Available extensions: vector, vectorscale, uuid-ossp, pgcrypto';
    RAISE NOTICE 'Created schemas: ai_data, embeddings, agents';
END $$;



