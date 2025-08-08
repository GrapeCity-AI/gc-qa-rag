# PgVector HTTP Adapter

A lightweight HTTP service that exposes PostgreSQL + pgvector functionality through Qdrant-compatible API endpoints.

## Purpose

This adapter serves as a transparent middleware layer that allows existing applications designed for Qdrant to work seamlessly with PostgreSQL + pgvector without code changes.

## Features

- **Qdrant API Compatibility**: Implements core Qdrant HTTP endpoints
- **Lightweight Design**: No heavy ML dependencies, vectors provided by caller
- **Hybrid Search**: Combines dense vector search with BM25 text search
- **Reciprocal Rank Fusion (RRF)**: Advanced result fusion algorithm
- **PostgreSQL Native**: Leverages PostgreSQL's full-text search and pgvector extension
- **Production Ready**: Includes health checks, logging, and connection pooling

## Architecture

```
ETL System -> HTTP (port 6333) -> PgVector Adapter -> PostgreSQL + pgvector
```

The adapter exposes port 6333 (Qdrant's default) and translates HTTP requests to PostgreSQL operations.

**Key Design Decision**: This adapter does NOT perform embedding computation. Vectors must be computed by the calling application (via AI services). This keeps the adapter lightweight (~50MB) vs embedding-enabled solutions (~3GB).

## Supported Endpoints

### Collection Management
- `GET /collections` - List collections
- `PUT /collections/{name}` - Create collection
- `GET /collections/{name}` - Get collection info
- `DELETE /collections/{name}` - Delete collection

### Point Operations
- `PUT /collections/{name}/points` - Upsert points
- `POST /collections/{name}/points/delete` - Delete points
- `POST /collections/{name}/points/search` - Vector search
- `POST /collections/{name}/points/scroll` - Scroll through points

### Custom Endpoints
- `POST /collections/{name}/points/search/hybrid` - Hybrid search (dense + sparse)

### System
- `GET /` - Cluster info
- `GET /health` - Health check
- `GET /telemetry` - Telemetry data

## Configuration

Environment variables (see `config.env.template`):

```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DATABASE=vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## Quick Start

1. **Build the image**:
   ```bash
   docker build -t pgvector-http-adapter .
   ```

2. **Run with PostgreSQL**:
   ```bash
   docker run -d \
     --name pgvector-adapter \
     -p 6333:6333 \
     -e POSTGRES_HOST=your-postgres-host \
     pgvector-http-adapter
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:6333/health
   ```

## Integration

To use with existing Qdrant-compatible applications:

1. Start the PgVector HTTP Adapter on port 6333
2. Ensure PostgreSQL with pgvector is running
3. Point your application to `http://localhost:6333`
4. No code changes required in your application

## Dependencies

- FastAPI - Lightweight web framework
- asyncpg - PostgreSQL async driver
- numpy - Basic vector operations
- pydantic - Data validation
- requests - HTTP client utilities

**Total package size: ~50MB** (vs ~3GB with ML libraries)

## Performance Notes

- Uses connection pooling for PostgreSQL
- Async operations throughout
- HNSW indexes for vector search
- GIN indexes for text search
- Configurable fusion weights for hybrid search

## Limitations

- Basic filter support (can be extended)
- No distributed clustering (single PostgreSQL instance)
- Vectors must be provided by caller (no built-in embedding)
- Requires external AI service for text-to-vector conversion

## Security

- Runs as non-root user
- Input validation via Pydantic
- Configurable CORS settings
- Health check endpoint for monitoring