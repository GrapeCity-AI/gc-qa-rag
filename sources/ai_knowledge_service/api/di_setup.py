"""
DI Setup - Dependency injection container configuration.

Centralizes the registration of all services for the application.
"""

import logging
from typing import Dict

from ai_knowledge_service.abstractions.execution.executor import (
    IIngestionExecutor,
    IIndexingExecutor,
    IPublishingExecutor,
)
from ai_knowledge_service.abstractions.execution.queue import ITaskQueue
from ai_knowledge_service.abstractions.infrastructure.event_bus import IEventBus
from ai_knowledge_service.abstractions.infrastructure.version_manager import IVersionManager
from ai_knowledge_service.abstractions.pipelines.source import ISourceConnector
from ai_knowledge_service.abstractions.storage.index_storage import IIndexStorage
from ai_knowledge_service.abstractions.storage.raw_file_storage import (
    IRawFileContentStore,
    IRawFileMetadataStore,
    IRawFileStorage,
)
from ai_knowledge_service.api.config import AppSettings
from ai_knowledge_service.core.executors.indexing_executor import IndexingExecutor
from ai_knowledge_service.core.executors.ingestion_executor import IngestionExecutor
from ai_knowledge_service.core.executors.publishing_executor import PublishingExecutor
from ai_knowledge_service.implementations.connectors.filesystem_connector import (
    FilesystemConnector,
)
from ai_knowledge_service.implementations.infrastructure.memory_event_bus import (
    MemoryEventBus,
)
from ai_knowledge_service.implementations.infrastructure.memory_queue import (
    MemoryTaskQueue,
)
from ai_knowledge_service.implementations.infrastructure.simple_container import (
    SimpleContainer,
)
from ai_knowledge_service.implementations.infrastructure.sqlite_version_manager import (
    SqliteVersionManager,
)
from ai_knowledge_service.implementations.llm.llm_client import LLMClient, LLMConfig
from ai_knowledge_service.implementations.steps.chunkers import SentenceChunker
from ai_knowledge_service.implementations.steps.embedders import (
    DashScopeConfig,
    DashScopeEmbedder,
)
from ai_knowledge_service.implementations.steps.enrichers import QAEnricher
from ai_knowledge_service.implementations.steps.index_builders import VectorIndexBuilder
from ai_knowledge_service.implementations.steps.parsers import MarkItDownParser
from ai_knowledge_service.implementations.storage.composite_raw_file_storage import (
    CompositeRawFileStorage,
)
from ai_knowledge_service.implementations.storage.filesystem_content_store import (
    FilesystemContentStore,
)
from ai_knowledge_service.implementations.storage.qdrant_index_storage import (
    QdrantConfig,
    QdrantIndexStorage,
)
from ai_knowledge_service.implementations.storage.sqlite_metadata_store import (
    SqliteMetadataStore,
)


logger = logging.getLogger(__name__)


def setup_container(settings: AppSettings) -> SimpleContainer:
    """
    Set up the dependency injection container with all services.

    Args:
        settings: Application settings.

    Returns:
        SimpleContainer: Configured DI container.
    """
    container = SimpleContainer()

    # Ensure storage directories exist
    settings.ensure_directories()

    # === 1. Infrastructure ===
    event_bus = MemoryEventBus()
    container.register_instance(IEventBus, event_bus)

    task_queue = MemoryTaskQueue()
    container.register_instance(ITaskQueue, task_queue)

    version_manager = SqliteVersionManager(settings.storage.versions_db_path)
    container.register_instance(IVersionManager, version_manager)

    logger.info("Registered infrastructure services")

    # === 2. Storage ===
    metadata_store = SqliteMetadataStore(settings.storage.metadata_db_path)
    container.register_instance(IRawFileMetadataStore, metadata_store)

    content_store = FilesystemContentStore(settings.storage.raw_files_path)
    container.register_instance(IRawFileContentStore, content_store)

    raw_file_storage = CompositeRawFileStorage(
        metadata_store=metadata_store,
        content_store=content_store,
    )
    container.register_instance(IRawFileStorage, raw_file_storage)

    qdrant_config = QdrantConfig(
        url=settings.qdrant.url,
        api_key=settings.qdrant.api_key,
        timeout=settings.qdrant.timeout,
    )
    index_storage = QdrantIndexStorage(qdrant_config)
    container.register_instance(IIndexStorage, index_storage)

    logger.info("Registered storage services")

    # === 3. LLM Client ===
    llm_config = LLMConfig(
        api_key=settings.llm.api_key,
        api_base=settings.llm.base_url,
        model_name=settings.llm.model,
    )
    llm_client = LLMClient(llm_config)

    # === 4. Processing Steps ===
    steps: Dict[str, object] = {}

    # Parsers
    markitdown_parser = MarkItDownParser()
    steps["markitdown_parser"] = markitdown_parser

    # Chunkers
    sentence_chunker = SentenceChunker()
    steps["sentence_chunker"] = sentence_chunker

    # Enrichers
    qa_enricher = QAEnricher(llm_client=llm_client)
    steps["qa_enricher"] = qa_enricher

    # Embedders
    dashscope_config = DashScopeConfig(
        api_key=settings.embedding.api_key,
        model_name=settings.embedding.model_name,
        dimensions=settings.embedding.dimensions,
    )
    dashscope_embedder = DashScopeEmbedder(config=dashscope_config)
    steps["dashscope_embedder"] = dashscope_embedder

    # Index builders
    vector_index_builder = VectorIndexBuilder()
    steps["vector_index_builder"] = vector_index_builder

    logger.info(f"Registered {len(steps)} processing steps")

    # === 5. Connectors ===
    connectors: Dict[str, ISourceConnector] = {
        "filesystem": FilesystemConnector(),
    }

    logger.info(f"Registered {len(connectors)} connectors")

    # === 6. Executors ===
    ingestion_executor = IngestionExecutor(
        raw_file_storage=raw_file_storage,
        version_manager=version_manager,
        connectors=connectors,
    )
    container.register_instance(IIngestionExecutor, ingestion_executor)

    indexing_executor = IndexingExecutor(
        raw_file_storage=raw_file_storage,
        index_storage=index_storage,
        processing_steps=steps,
    )
    container.register_instance(IIndexingExecutor, indexing_executor)

    publishing_executor = PublishingExecutor(
        index_storage=index_storage,
    )
    container.register_instance(IPublishingExecutor, publishing_executor)

    logger.info("Registered executor services")

    return container


def get_processing_steps(container: SimpleContainer) -> Dict[str, object]:
    """
    Get all registered processing steps from the container.

    This is a convenience function for accessing the steps
    that were registered during container setup.

    Args:
        container: The DI container.

    Returns:
        Dict of step name to step instance.
    """
    # We don't register steps individually in the container,
    # but they are used by the IndexingExecutor.
    # This function is here for future extensibility.
    return {}
