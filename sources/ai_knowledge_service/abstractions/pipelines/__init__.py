"""
Pipelines module - Pipeline and processing step interfaces.
"""

from ai_knowledge_service.abstractions.pipelines.source import (
    ISourceConnector,
    SourceConfig,
    SourceRecord,
    ConnectionResult,
    ConnectionStatus,
)

from ai_knowledge_service.abstractions.pipelines.steps import (
    IProcessingStep,
    IContentParser,
    IChunker,
    IEnricher,
    IEmbedder,
    IIndexBuilder,
    ProcessingContext,
    ParsedDocument,
    Chunk,
    Embedding,
)

from ai_knowledge_service.abstractions.pipelines.publishing import (
    ITargetEnvironment,
    IIndexExporter,
    IIndexImporter,
    IRawFileExporter,
    EnvironmentCapabilities,
    ExportOptions,
    ExportResult,
    ImportOptions,
    ImportResult,
)

__all__ = [
    # Source
    "ISourceConnector",
    "SourceConfig",
    "SourceRecord",
    "ConnectionResult",
    "ConnectionStatus",
    # Steps
    "IProcessingStep",
    "IContentParser",
    "IChunker",
    "IEnricher",
    "IEmbedder",
    "IIndexBuilder",
    "ProcessingContext",
    "ParsedDocument",
    "Chunk",
    "Embedding",
    # Publishing
    "ITargetEnvironment",
    "IIndexExporter",
    "IIndexImporter",
    "IRawFileExporter",
    "EnvironmentCapabilities",
    "ExportOptions",
    "ExportResult",
    "ImportOptions",
    "ImportResult",
]
