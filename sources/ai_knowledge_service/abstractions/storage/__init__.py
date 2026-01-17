"""
Storage module - Storage interfaces for raw files and indexes.
"""

from ai_knowledge_service.abstractions.storage.raw_file_storage import (
    IRawFileStorage,
    IRawFileMetadataStore,
    IRawFileContentStore,
    QueryCriteria,
)

from ai_knowledge_service.abstractions.storage.index_storage import (
    IIndexStorage,
    WriteResult,
    CollectionInfo,
)

__all__ = [
    # Raw File Storage
    "IRawFileStorage",
    "IRawFileMetadataStore",
    "IRawFileContentStore",
    "QueryCriteria",
    # Index Storage
    "IIndexStorage",
    "WriteResult",
    "CollectionInfo",
]
