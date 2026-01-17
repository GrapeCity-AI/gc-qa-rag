"""
Example: Run Generic Pipeline

This example demonstrates how to use the AI Knowledge Service
to run a complete Generic ETL pipeline:
  1. Ingestion - Fetch files from filesystem
  2. Indexing - Parse, chunk, enrich with QA, embed, build index
  3. Publishing - Update alias for blue-green deployment

Prerequisites:
  - Qdrant running (docker run -p 6333:6333 qdrant/qdrant)
  - DashScope API key (for embeddings)
  - OpenAI-compatible LLM API (for QA generation)
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_dotenv(env_path: Path = None):
    """Load environment variables from .env file (overwrites existing)."""
    if env_path is None:
        # Look for .env in the ai_knowledge_service directory
        env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            # Strip whitespace and Windows line endings
            line = line.strip().replace("\r", "")
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key:
                    os.environ[key] = value
                    print(f"Loaded env: {key}={value[:10]}..." if len(value) > 10 else f"Loaded env: {key}={value}")


# Load .env file before anything else
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_services():
    """Create and configure all required services."""

    # === Storage Services ===
    from ai_knowledge_service.implementations.storage import (
        FilesystemContentStore,
        SqliteMetadataStore,
        CompositeRawFileStorage,
        QdrantIndexStorage,
        QdrantConfig,
    )

    # Raw file storage (content + metadata)
    content_store = FilesystemContentStore(base_path="./.gc-qa-rag-data/content")
    metadata_store = SqliteMetadataStore(db_path="./.gc-qa-rag-data/metadata.db")
    raw_storage = CompositeRawFileStorage(metadata_store, content_store)

    # Vector index storage (Qdrant)
    qdrant_config = QdrantConfig(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )
    index_storage = QdrantIndexStorage(qdrant_config)

    # === LLM Client (for QA generation) ===
    from ai_knowledge_service.implementations.llm import LLMClient, LLMConfig

    llm_config = LLMConfig(
        api_key=os.getenv("LLM_API_KEY", "your-api-key"),
        api_base=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
        model_name=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        max_rpm=30,
    )
    llm_client = LLMClient(llm_config)

    # === Source Connectors ===
    from ai_knowledge_service.implementations.connectors import FilesystemConnector

    connectors = {
        "filesystem": FilesystemConnector(),
    }

    # === Processing Steps ===
    from ai_knowledge_service.implementations.steps.parsers import MarkItDownParser
    from ai_knowledge_service.implementations.steps.chunkers import SentenceChunker
    from ai_knowledge_service.implementations.steps.enrichers import QAEnricher
    from ai_knowledge_service.implementations.steps.embedders import DashScopeEmbedder, DashScopeConfig
    from ai_knowledge_service.implementations.steps.index_builders import VectorIndexBuilder

    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "your-dashscope-key")
    logger.info(f"DashScope API Key: {dashscope_api_key[:10]}... (len={len(dashscope_api_key)})")

    dashscope_config = DashScopeConfig(
        api_key=dashscope_api_key,
        model_name="text-embedding-v4",
        dimensions=1024,
    )

    steps = {
        "markitdown_parser": MarkItDownParser(),
        "sentence_chunker": SentenceChunker(),
        "qa_enricher": QAEnricher(llm_client),
        "dashscope_embedder": DashScopeEmbedder(dashscope_config),
        "vector_index_builder": VectorIndexBuilder(),
    }

    # === Executors ===
    from ai_knowledge_service.core.executors import (
        IngestionExecutor,
        IndexingExecutor,
        PublishingExecutor,
    )

    ingestion_executor = IngestionExecutor(raw_storage, connectors)
    indexing_executor = IndexingExecutor(raw_storage, index_storage, steps)
    publishing_executor = PublishingExecutor(index_storage)

    return {
        "raw_storage": raw_storage,
        "index_storage": index_storage,
        "ingestion_executor": ingestion_executor,
        "indexing_executor": indexing_executor,
        "publishing_executor": publishing_executor,
    }


def run_ingestion(services: dict, source_path: str, kb_id: str, kb_version_id: str):
    """Run ingestion to fetch files from source."""
    from ai_knowledge_service.abstractions.models.tasks import IngestionTask

    logger.info(f"=== Starting Ingestion from {source_path} ===")

    task = IngestionTask(
        id=f"ingest-{kb_version_id}",
        knowledge_base_id=kb_id,
        knowledge_base_version_id=kb_version_id,
        source_config={
            "connector_type": "filesystem",
            "connection_params": {
                "path": source_path,
                "recursive": True,
            },
            "fetch_options": {
                "extensions": [".txt", ".md", ".pdf", ".docx"],
            },
        },
    )

    result = services["ingestion_executor"].execute(task)

    logger.info(f"Ingestion completed: {result.status}")
    logger.info(f"  New files: {result.new_files_count}")
    logger.info(f"  Updated files: {result.updated_files_count}")
    logger.info(f"  Unchanged files: {result.unchanged_files_count}")
    logger.info(f"  Total ingested: {len(result.ingested_file_ids)}")

    return result


def run_indexing(services: dict, kb_id: str, kb_version_id: str, minimal: bool = False):
    """Run indexing pipeline on ingested files."""
    from ai_knowledge_service.abstractions.models.tasks import IndexingTask, StepConfig

    logger.info("=== Starting Indexing Pipeline ===")

    # Note: The IndexingExecutor will automatically create the collection
    # using the naming convention: kb_{kb_id}_{version_id}

    # Build pipeline config based on mode
    if minimal:
        logger.info("Running minimal pipeline (parse + chunk only)")
        pipeline_config = [
            StepConfig(step_type="markitdown_parser"),
            StepConfig(step_type="sentence_chunker", config={
                "group_size": 3,
                "min_group_size": 2,
                "max_chunk_size": 2000,
            }),
            # Skip QA enricher, embedder, and index builder in minimal mode
        ]
    else:
        pipeline_config = [
            StepConfig(step_type="markitdown_parser"),
            StepConfig(step_type="sentence_chunker", config={
                "group_size": 3,
                "min_group_size": 2,
                "max_chunk_size": 2000,
            }),
            StepConfig(step_type="qa_enricher", config={
                "multi_chunk_threshold": 2,
            }),
            StepConfig(step_type="dashscope_embedder", config={
                "embed_questions": True,
                "embed_answers": True,
            }),
            StepConfig(step_type="vector_index_builder"),
        ]

    task = IndexingTask(
        id=f"index-{kb_version_id}",
        knowledge_base_id=kb_id,
        knowledge_base_version_id=kb_version_id,
        pipeline_config=pipeline_config,
    )

    result = services["indexing_executor"].execute(task)

    logger.info(f"Indexing completed: {result.status}")
    logger.info(f"  Index records created: {result.index_records_count}")
    logger.info(f"  Collections affected: {result.collections_affected}")
    if result.step_stats:
        for step_type, stats in result.step_stats.items():
            logger.info(f"  {step_type}: input={stats.input_count}, output={stats.output_count}")

    return result


def run_publishing(services: dict, kb_id: str, kb_version_id: str):
    """Publish the indexed version by updating alias."""
    from ai_knowledge_service.abstractions.models.tasks import PublishingTask

    logger.info("=== Starting Publishing ===")

    # The collection name is derived by the executor: kb_{kb_id}_{version_id}
    alias_name = f"{kb_id}-latest"

    task = PublishingTask(
        id=f"publish-{kb_version_id}",
        knowledge_base_id=kb_id,
        knowledge_base_version_id=kb_version_id,
        target_environment_id="local",
        alias_name=alias_name,
    )

    result = services["publishing_executor"].execute(task)

    logger.info(f"Publishing completed: {result.status}")
    logger.info(f"  Alias '{alias_name}' now points to '{result.target_collection}'")

    return result


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Generic ETL Pipeline")
    parser.add_argument("--source", required=True, help="Source directory path")
    parser.add_argument("--kb-id", default="my-kb", help="Knowledge base ID")
    parser.add_argument("--kb-version", default="v1", help="Knowledge base version ID")
    parser.add_argument("--step", choices=["all", "ingest", "index", "publish"], default="all",
                        help="Which step to run")
    parser.add_argument("--minimal", action="store_true",
                        help="Run minimal pipeline (parse + chunk only, no QA/embedding)")

    args = parser.parse_args()

    # Validate source path
    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"Source path does not exist: {source_path}")
        return 1

    # Create data directory
    Path("./.gc-qa-rag-data/content").mkdir(parents=True, exist_ok=True)

    # Initialize services
    logger.info("Initializing services...")
    services = create_services()

    # Run pipeline steps
    if args.step in ["all", "ingest"]:
        run_ingestion(services, str(source_path), args.kb_id, args.kb_version)

    if args.step in ["all", "index"]:
        run_indexing(services, args.kb_id, args.kb_version, minimal=args.minimal)

    if args.step in ["all", "publish"]:
        run_publishing(services, args.kb_id, args.kb_version)

    logger.info("=== Pipeline Complete ===")
    return 0


if __name__ == "__main__":
    exit(main())
