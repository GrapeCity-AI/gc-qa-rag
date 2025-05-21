from typing import Optional, Dict, Any


class BaseContext:
    """Base context class containing common attributes for all context types."""

    def __init__(self, root_path: str, doc_type: str, product: str) -> None:
        """
        Initialize base context with common attributes.

        Args:
            root_path: Root directory path for operations
            doc_type: Type of document being processed
            product: Product name being processed
        """
        self.root = root_path
        self.doc_type = doc_type
        self.product = product


class EtlContext(BaseContext):
    """Context class for ETL (Extract, Transform, Load) operations."""

    def __init__(
        self,
        root_path: str,
        doc_type: str,
        product: str,
        index: str,
        thread_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize ETL context with additional ETL-specific attributes.

        Args:
            root_path: Root directory path for operations
            doc_type: Type of document being processed
            product: Product name being processed
            index: Index for processing
            thread_dict: Optional dictionary for thread-specific data
        """
        super().__init__(root_path, doc_type, product)
        self.index = index
        self.thread_dict = thread_dict


class EtlRagContext(BaseContext):
    """Context class for RAG (Retrieval Augmented Generation) operations."""

    def __init__(
        self, root_path: str, doc_type: str, product: str, base_url: str, tag: str
    ) -> None:
        """
        Initialize RAG context with additional RAG-specific attributes.

        Args:
            root_path: Root directory path for operations
            doc_type: Type of document being processed
            product: Product name being processed
            base_url: Base URL for vector database
            tag: Tag for collection identification
        """
        super().__init__(root_path, doc_type, product)
        self.base_url = base_url
        self.tag = tag
