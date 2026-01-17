# AI Knowledge Service

ETL abstraction layer for AI knowledge base management.

## Features

- **Ingestion**: Fetch documents from various sources (filesystem, etc.)
- **Indexing**: Parse, chunk, enrich with QA, embed, and build vector indexes
- **Publishing**: Blue-green deployment with alias management

## Installation

```bash
pdm install
```

## Usage

```bash
# Set environment variables
export LLM_API_KEY="your-api-key"
export DASHSCOPE_API_KEY="your-dashscope-key"

# Run pipeline
pdm run python examples/run_generic_pipeline.py --source /path/to/docs --kb-id my-kb --kb-version v1
```

## Development

```bash
# Run tests
pdm run pytest

# Run tests with coverage
pdm run pytest --cov=ai_knowledge_service
```
