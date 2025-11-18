-- Initialize pgvector extension for VietMindAI-ADK
-- This script runs automatically when the PostgreSQL container is first created

-- Create vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Create schema if needed (optional)
-- CREATE SCHEMA IF NOT EXISTS mindai;

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON DATABASE mindai_adk TO mindai_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO mindai_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension initialized successfully';
    RAISE NOTICE 'Database: mindai_adk';
    RAISE NOTICE 'User: mindai_user';
    RAISE NOTICE 'Ready for vector operations with 768-dimensional embeddings';
END $$;
