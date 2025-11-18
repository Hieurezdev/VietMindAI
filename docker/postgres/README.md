# PostgreSQL with pgvector - Docker Setup

This directory contains the Docker setup for PostgreSQL with pgvector extension for VietMindAI-ADK.

## Quick Start

### 1. Start the Database

```bash
# From project root
docker-compose -f docker-compose.postgres.yml up -d

# Check logs
docker-compose -f docker-compose.postgres.yml logs -f postgres

# Verify pgvector extension
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

### 2. Configure Environment

Update your `.env` file with the database connection string:

```bash
DATABASE_URL=postgresql+asyncpg://mindai_user:mindai_password@localhost:5432/mindai_adk
```

### 3. Run Migrations

```bash
# From project root
uv run alembic upgrade head
```

### 4. Verify Setup

```bash
# Check tables
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "\dt"

# Check indexes
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "\di"

# Check knowledge_chunks table
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "\d+ knowledge_chunks"
```

## Services

### PostgreSQL (port 5432)
- **Image**: `pgvector/pgvector:pg16`
- **Database**: `mindai_adk`
- **User**: `mindai_user`
- **Password**: `mindai_password`
- **Container**: `vietmindai-postgres`

### pgAdmin (port 8080)
- **URL**: http://localhost:8080
- **Email**: admin@vietmindai.com
- **Password**: admin123

To connect pgAdmin to PostgreSQL:
1. Open http://localhost:8080
2. Add New Server:
   - Name: VietMindAI
   - Host: postgres (or `host.docker.internal` on Mac/Windows)
   - Port: 5432
   - Database: mindai_adk
   - Username: mindai_user
   - Password: mindai_password

## Directory Structure

```
docker/postgres/
├── init/                    # Initialization scripts (run once on first startup)
│   └── 01-init-pgvector.sql # Enable pgvector extension
├── backups/                 # Database backups directory
└── README.md               # This file
```

## Common Operations

### Backup Database

```bash
# Create backup
docker exec vietmindai-postgres pg_dump -U mindai_user mindai_adk > docker/postgres/backups/backup_$(date +%Y%m%d_%H%M%S).sql

# With compression
docker exec vietmindai-postgres pg_dump -U mindai_user mindai_adk | gzip > docker/postgres/backups/backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore Database

```bash
# From SQL file
docker exec -i vietmindai-postgres psql -U mindai_user -d mindai_adk < docker/postgres/backups/backup.sql

# From compressed file
gunzip -c docker/postgres/backups/backup.sql.gz | docker exec -i vietmindai-postgres psql -U mindai_user -d mindai_adk
```

### Connect to Database

```bash
# Using psql in container
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk

# From host (if psql is installed)
psql postgresql://mindai_user:mindai_password@localhost:5432/mindai_adk
```

### View Logs

```bash
# Postgres logs
docker-compose -f docker-compose.postgres.yml logs postgres

# Follow logs
docker-compose -f docker-compose.postgres.yml logs -f postgres

# Last 100 lines
docker-compose -f docker-compose.postgres.yml logs --tail=100 postgres
```

### Stop/Start Services

```bash
# Stop all services
docker-compose -f docker-compose.postgres.yml stop

# Start services
docker-compose -f docker-compose.postgres.yml start

# Restart services
docker-compose -f docker-compose.postgres.yml restart

# Stop and remove containers (data persists)
docker-compose -f docker-compose.postgres.yml down

# Stop and remove containers AND volumes (deletes all data)
docker-compose -f docker-compose.postgres.yml down -v
```

### Reset Database

```bash
# WARNING: This deletes all data!

# Stop and remove containers and volumes
docker-compose -f docker-compose.postgres.yml down -v

# Start fresh
docker-compose -f docker-compose.postgres.yml up -d

# Run migrations
uv run alembic upgrade head
```

## Troubleshooting

### Port 5432 Already in Use

If you have another PostgreSQL instance running:

```bash
# Option 1: Stop local PostgreSQL
sudo systemctl stop postgresql  # Linux
brew services stop postgresql   # macOS

# Option 2: Change port in docker-compose.postgres.yml
# Change "5432:5432" to "5433:5432" and update DATABASE_URL
```

### Container Won't Start

```bash
# Check logs
docker logs vietmindai-postgres

# Remove old container
docker rm -f vietmindai-postgres

# Try again
docker-compose -f docker-compose.postgres.yml up -d
```

### pgvector Extension Not Found

```bash
# Manually enable extension
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Verify
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

### Permission Denied

```bash
# Grant permissions
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mindai_user;"
docker exec -it vietmindai-postgres psql -U mindai_user -d mindai_adk -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mindai_user;"
```

### Data Persistence

Data is stored in Docker volumes:
- `postgres_data`: Database files
- `pgadmin_data`: pgAdmin configuration

View volumes:
```bash
docker volume ls | grep vietmindai
docker volume inspect vietmindai-adk_postgres_data
```

## Performance Tuning

For production use, consider adjusting PostgreSQL settings in `docker-compose.postgres.yml`:

```yaml
environment:
  # ... existing env vars ...
  # Memory settings
  POSTGRES_SHARED_BUFFERS: 256MB
  POSTGRES_EFFECTIVE_CACHE_SIZE: 1GB
  POSTGRES_WORK_MEM: 16MB
  POSTGRES_MAINTENANCE_WORK_MEM: 128MB

  # Connection settings
  POSTGRES_MAX_CONNECTIONS: 100

  # Performance
  POSTGRES_RANDOM_PAGE_COST: 1.1
```

## Security Notes

**IMPORTANT**: The default credentials are for development only!

For production:
1. Change default passwords in `docker-compose.postgres.yml`
2. Use environment variables or secrets
3. Enable SSL/TLS connections
4. Restrict network access
5. Set up regular backups
6. Enable connection encryption

## Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker PostgreSQL Image](https://hub.docker.com/_/postgres)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
