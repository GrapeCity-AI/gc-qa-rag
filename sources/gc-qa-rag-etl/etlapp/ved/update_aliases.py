from typing import List, Tuple
import logging
from etlapp.common.vector import VectorClient

logger = logging.getLogger(__name__)

# Configuration for collection aliases
COLLECTION_ALIASES = {
    "doc": [
        ("doc_forguncy_{tag}", "doc_forguncy_prod"),
        ("doc_wyn_{tag}", "doc_wyn_prod"),
        ("doc_spreadjs_{tag}", "doc_spreadjs_prod"),
        ("doc_gcexcel_{tag}", "doc_gcexcel_prod"),
    ],
    "forum_qa": [
        ("forum_qa_forguncy_{tag}", "forum_qa_forguncy_prod"),
        ("forum_qa_wyn_{tag}", "forum_qa_wyn_prod"),
        ("forum_qa_spreadjsgcexcel_{tag}", "forum_qa_spreadjsgcexcel_prod"),
    ],
    "forum_tutorial": [
        ("forum_tutorial_forguncy_{tag}", "forum_tutorial_forguncy_prod"),
        ("forum_tutorial_wyn_{tag}", "forum_tutorial_wyn_prod"),
        ("forum_tutorial_spreadjsgcexcel_{tag}", "forum_tutorial_spreadjsgcexcel_prod"),
    ],
}


def update_alias_pairs(
    client: VectorClient, alias_pairs: List[Tuple[str, str]], tag: str = None
) -> None:
    """
    Update a list of collection aliases.

    Args:
        client: VectorClient instance
        alias_pairs: List of (source_collection, target_alias) tuples
        tag: Optional tag to replace in collection names
    """
    for source, target in alias_pairs:
        try:
            # Replace {tag} placeholder if present
            source_collection = source.format(tag=tag) if tag else source
            client.update_collection_aliases(source_collection, target)
            logger.info(f"Successfully updated alias: {source_collection} -> {target}")
        except Exception as e:
            logger.error(
                f"Failed to update alias {source_collection} -> {target}: {str(e)}"
            )


def start_update_aliases(url: str, tag: str) -> None:
    """
    Start the process of updating collection aliases.

    Args:
        url: URL of the vector database
        tag: Tag identifier for the update process
    """
    logger.info(f"Starting alias updates with tag: {tag}")
    client = VectorClient(url)

    try:
        # Update doc collection aliases
        update_alias_pairs(client, COLLECTION_ALIASES["doc"], tag)

        # Update forum QA collection aliases
        update_alias_pairs(client, COLLECTION_ALIASES["forum_qa"], tag)

        # Update forum tutorial collection aliases
        update_alias_pairs(client, COLLECTION_ALIASES["forum_tutorial"], tag)

        logger.info("All alias updates completed successfully")
    except Exception as e:
        logger.error(f"Failed to complete alias updates: {str(e)}")
        raise
