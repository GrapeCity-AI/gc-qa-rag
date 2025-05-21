from typing import Protocol
from etlapp.common.context import EtlContext
from etlapp.etl.etl_doc.embedding import start_embedding_doc
from etlapp.etl.etl_doc.generate import start_generate_doc
from etlapp.etl.etl_doc.generate_full import start_generate_full_doc
from etlapp.etl.etl_doc.generate_sub import start_generate_sub_doc
from etlapp.etl.etl_doc.merge import start_merge_doc
from etlapp.etl.etl_forum_qa.embedding import start_embedding_forum_qa
from etlapp.etl.etl_forum_qa.generate import start_generate_forum_qa
from etlapp.etl.etl_forum_tutorial.embedding import start_embedding_forum_tutorial
from etlapp.etl.etl_forum_tutorial.generate import start_generate_forum_tutorial
from etlapp.etl.etl_generic.generate import start_generate_generic
from etlapp.etl.etl_generic.generate_sub import start_generate_sub_generic
from etlapp.etl.etl_generic.merge import start_merge_generic
from etlapp.etl.etl_generic.embedding import start_embedding_generic
from etlapp.etl.etl_generic.generate_full import start_generate_full_generic


class EtlFlow(Protocol):
    """Protocol defining the interface for ETL flows."""

    def execute(self, context: EtlContext) -> None:
        """Execute the ETL flow with the given context."""
        ...


class BaseEtlFlow:
    """Base class for ETL flows providing common functionality."""

    def __init__(self, name: str):
        self.name = name

    def execute(self, context: EtlContext) -> None:
        """Execute the ETL flow with the given context."""
        raise NotImplementedError("Subclasses must implement execute()")


class DocEmbeddingFlow(BaseEtlFlow):
    """ETL flow for document embedding processing."""

    def __init__(self, generate_sub: bool = False):
        super().__init__("doc_embedding")
        self.generate_sub = generate_sub

    def execute(self, context: EtlContext) -> None:
        """Execute the document embedding flow.

        Args:
            context: The ETL context containing necessary parameters
        """
        start_generate_doc(context)
        if self.generate_sub:
            start_generate_sub_doc(context)
        start_merge_doc(context)
        start_embedding_doc(context)


class DocFullFlow(BaseEtlFlow):
    """ETL flow for full document processing."""

    def __init__(self):
        super().__init__("doc_full")

    def execute(self, context: EtlContext) -> None:
        """Execute the full document processing flow.

        Args:
            context: The ETL context containing necessary parameters
        """
        start_generate_full_doc(context)


class ForumQaEmbeddingFlow(BaseEtlFlow):
    """ETL flow for forum Q&A embedding processing."""

    def __init__(self):
        super().__init__("forum_qa_embedding")

    def execute(self, context: EtlContext) -> None:
        """Execute the forum Q&A embedding flow.

        Args:
            context: The ETL context containing necessary parameters
        """
        start_generate_forum_qa(context)
        start_embedding_forum_qa(context)


class ForumTutorialEmbeddingFlow(BaseEtlFlow):
    """ETL flow for forum tutorial embedding processing."""

    def __init__(self):
        super().__init__("forum_tutorial_embedding")

    def execute(self, context: EtlContext) -> None:
        """Execute the forum tutorial embedding flow.

        Args:
            context: The ETL context containing necessary parameters
        """
        start_generate_forum_tutorial(context)
        start_embedding_forum_tutorial(context)


class GenericEmbeddingFlow(BaseEtlFlow):
    def __init__(self, generate_sub: bool = False):
        super().__init__("generic_embedding")
        self.generate_sub = generate_sub

    def execute(self, context: EtlContext) -> None:
        start_generate_generic(context)
        if self.generate_sub:
            start_generate_sub_generic(context)
        start_merge_generic(context)
        start_embedding_generic(context)


class GenericFullFlow(BaseEtlFlow):
    def __init__(self):
        super().__init__("generic_full")

    def execute(self, context: EtlContext) -> None:
        start_generate_full_generic(context)


# Factory function to get the appropriate flow
def get_etl_flow(doc_type: str, mode: str = None) -> EtlFlow:
    """Get the appropriate ETL flow based on document type and mode.

    Args:
        doc_type: Type of document to process
        mode: Optional processing mode

    Returns:
        An instance of the appropriate ETL flow

    Raises:
        ValueError: If the document type or mode is invalid
    """
    if doc_type == "doc":
        if mode == "full":
            return DocFullFlow()
        return DocEmbeddingFlow()
    elif doc_type == "forum/qa":
        return ForumQaEmbeddingFlow()
    elif doc_type == "forum/tutorial":
        return ForumTutorialEmbeddingFlow()
    elif doc_type == "generic":
        return GenericEmbeddingFlow()
    else:
        raise ValueError(f"Invalid document type: {doc_type}")


# Legacy functions for backward compatibility
def etl_doc_embedding_flow(context: EtlContext) -> None:
    """Legacy function for document embedding flow."""
    DocEmbeddingFlow().execute(context)


def etl_doc_full_flow(context: EtlContext) -> None:
    """Legacy function for full document flow."""
    DocFullFlow().execute(context)


def etl_forum_qa_embedding_flow(context: EtlContext) -> None:
    """Legacy function for forum Q&A embedding flow."""
    ForumQaEmbeddingFlow().execute(context)


def etl_forum_tutorial_embedding_flow(context: EtlContext) -> None:
    """Legacy function for forum tutorial embedding flow."""
    ForumTutorialEmbeddingFlow().execute(context)


def etl_generic_embedding_flow(context: EtlContext) -> None:
    GenericEmbeddingFlow().execute(context)


def etl_generic_full_flow(context: EtlContext) -> None:
    GenericFullFlow().execute(context)
