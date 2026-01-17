"""
Processing Steps interfaces - Defines the processing pipeline steps.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ai_knowledge_service.abstractions.models.raw_file import RawFile
from ai_knowledge_service.abstractions.models.knowledge_base import FileVersion
from ai_knowledge_service.abstractions.models.index import IndexRecord
from ai_knowledge_service.abstractions.models.tasks import ProcessingError


@dataclass
class ParsedDocument:
    """
    Parsed Document - Result of content parsing.

    Contains the structured representation of a raw file.
    """

    title: str = ""
    content: str = ""  # Main text content
    sections: List["DocumentSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        """Get all text content combined."""
        parts = [self.content]
        for section in self.sections:
            parts.append(section.content)
        return "\n".join(filter(None, parts))

    @property
    def section_count(self) -> int:
        """Get number of sections."""
        return len(self.sections)


@dataclass
class DocumentSection:
    """A section within a parsed document."""

    title: str = ""
    content: str = ""
    level: int = 1  # Heading level (1-6)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """
    Chunk - A segment of content for processing.

    Chunks are the unit of processing for enrichment and embedding.
    """

    id: str
    content: str
    index: int  # Position in the sequence
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional: tracking original position
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

    def __post_init__(self):
        if not self.id:
            raise ValueError("Chunk ID cannot be empty")

    @property
    def length(self) -> int:
        """Get content length."""
        return len(self.content)


@dataclass
class Embedding:
    """
    Embedding - Vector representation of content.
    """

    id: str
    chunk_id: str  # Reference to source chunk
    vector: List[float]  # Dense vector
    sparse_vector: Optional[Dict[int, float]] = None  # Sparse vector
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Embedding ID cannot be empty")
        if not self.vector:
            raise ValueError("Vector cannot be empty")

    @property
    def dimensions(self) -> int:
        """Get vector dimensions."""
        return len(self.vector)

    @property
    def has_sparse(self) -> bool:
        """Check if sparse vector is available."""
        return self.sparse_vector is not None and len(self.sparse_vector) > 0


@dataclass
class ProcessingContext:
    """
    Processing Context - Carries data through the processing pipeline.

    Each processing step reads from and writes to this context.
    Errors are accumulated rather than thrown, supporting skip-and-continue.
    """

    raw_file: RawFile
    file_version: FileVersion

    # Raw content bytes (loaded by executor)
    raw_content: Optional[bytes] = None

    # Pipeline outputs (populated by different steps)
    parsed_document: Optional[ParsedDocument] = None
    chunks: Optional[List[Chunk]] = None
    enrichments: Dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[List[Embedding]] = None
    index_records: Optional[List[IndexRecord]] = None

    # Error handling
    errors: List[ProcessingError] = field(default_factory=list)
    should_skip: bool = False
    skip_reason: Optional[str] = None

    # Timing
    started_at: datetime = field(default_factory=datetime.now)

    def add_error(
        self,
        step: str,
        error_type: str,
        message: str,
        recoverable: bool = True,
    ) -> None:
        """Add an error to the context."""
        self.errors.append(ProcessingError(
            item_id=self.raw_file.id,
            item_name=self.raw_file.original_name,
            step=step,
            error_type=error_type,
            error_message=message,
            recoverable=recoverable,
        ))

    def mark_skip(self, reason: str) -> None:
        """Mark this context to skip remaining steps."""
        self.should_skip = True
        self.skip_reason = reason

    def get_enrichment(self, key: str, default: Any = None) -> Any:
        """Get an enrichment value."""
        return self.enrichments.get(key, default)

    def set_enrichment(self, key: str, value: Any) -> None:
        """Set an enrichment value."""
        self.enrichments[key] = value

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)


# Forward reference for ObservabilityContext (defined in observability module)
# This avoids circular imports
ObservabilityContext = Any


@runtime_checkable
class IProcessingStep(Protocol):
    """
    Processing Step - Base interface for all pipeline steps.

    Steps are composable units of processing that transform the context.
    Each step should:
    - Be stateless (configuration via configure())
    - Handle errors gracefully (add to context.errors)
    - Support observability (metrics, tracing)
    """

    @property
    def step_type(self) -> str:
        """
        Get the step type identifier.

        Returns:
            str: Unique identifier for this step type.
        """
        ...

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the step.

        Args:
            config: Step configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        ...

    def process(
        self,
        context: ProcessingContext,
        observability: ObservabilityContext,
    ) -> ProcessingContext:
        """
        Process the context.

        Args:
            context: The processing context.
            observability: Observability context for metrics/tracing.

        Returns:
            ProcessingContext: The updated context.
        """
        ...


@runtime_checkable
class IContentParser(IProcessingStep, Protocol):
    """
    Content Parser - Parses raw content into structured documents.

    Input: context.raw_file (content)
    Output: context.parsed_document
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """Get list of supported MIME types."""
        ...


@runtime_checkable
class IChunker(IProcessingStep, Protocol):
    """
    Chunker - Splits documents into chunks.

    Input: context.parsed_document
    Output: context.chunks
    """

    @property
    def max_chunk_size(self) -> int:
        """Get maximum chunk size."""
        ...

    @property
    def overlap_size(self) -> int:
        """Get chunk overlap size."""
        ...


@runtime_checkable
class IEnricher(IProcessingStep, Protocol):
    """
    Enricher - Generates derived content (QA, summary, etc.).

    Multiple enrichers can be chained together.

    Input: context.chunks (or context.parsed_document)
    Output: context.enrichments[enrichment_type]
    """

    @property
    def enrichment_type(self) -> str:
        """
        Get the type of enrichment produced.

        Examples: "qa", "summary", "translation", "entities"
        """
        ...

    @property
    def requires_chunks(self) -> bool:
        """Check if this enricher requires chunks."""
        ...


@runtime_checkable
class IEmbedder(IProcessingStep, Protocol):
    """
    Embedder - Generates vector embeddings.

    Input: context.chunks (and optionally context.enrichments)
    Output: context.embeddings
    """

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        ...

    @property
    def supports_sparse(self) -> bool:
        """Check if sparse embeddings are supported."""
        ...

    @property
    def model_name(self) -> str:
        """Get the embedding model name."""
        ...


@runtime_checkable
class IIndexBuilder(IProcessingStep, Protocol):
    """
    Index Builder - Builds index records from processed data.

    Input: context (all processed data)
    Output: context.index_records
    """

    @property
    def index_type(self) -> str:
        """Get the type of index built."""
        ...
