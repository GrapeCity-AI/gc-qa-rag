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

        # Update generic collection aliases for all existing generic collections
        update_generic_aliases(client, tag)

        logger.info("All alias updates completed successfully")
    except Exception as e:
        logger.error(f"Failed to complete alias updates: {str(e)}")
        raise


def update_generic_aliases(client: VectorClient, tag: str) -> None:
    """
    Update aliases for all generic collections that match the pattern.

    Args:
        client: VectorClient instance
        tag: Tag identifier for the update process
    """
    try:
        # Get all collections from the vector database
        collections_info = client.client.get_collections()
        generic_collections = []

        # Find all generic collections with the current tag
        for collection in collections_info.collections:
            collection_name = collection.name
            if collection_name.startswith("generic_") and collection_name.endswith(
                f"_{tag}"
            ):
                # Extract product name from collection name
                # Format: generic_{product}_{tag}
                parts = collection_name.split("_")
                if len(parts) >= 3:
                    product = "_".join(parts[1:-1])  # Handle products with underscores
                    source = f"generic_{product}_{tag}"
                    target = f"generic_{product}_prod"
                    generic_collections.append((source, target))

        if generic_collections:
            update_alias_pairs(client, generic_collections, None)  # Don't format again
            logger.info(
                f"Updated {len(generic_collections)} generic collection aliases"
            )
        else:
            logger.info("No generic collections found to update")

    except Exception as e:
        logger.error(f"Failed to update generic aliases: {str(e)}")
        # Don't raise here to not break the overall process
        pass


def start_update_aliases_by_product(url: str, product: str, tag: str) -> None:
    """
    Start the process of updating collection aliases for a specific product.

    Args:
        url: URL of the vector database
        product: Product name (forguncy, wyn, spreadjs, gcexcel, spreadjsgcexcel)
        tag: Tag identifier for the update process
    """
    logger.info(f"Starting alias updates for product: {product} with tag: {tag}")
    client = VectorClient(url)

    try:
        # Filter aliases for the specific product
        product_aliases = []

        # Check doc aliases
        for source, target in COLLECTION_ALIASES["doc"]:
            if product in source:
                product_aliases.append((source, target))

        # Check forum QA aliases
        for source, target in COLLECTION_ALIASES["forum_qa"]:
            if product in source:
                product_aliases.append((source, target))

        # Check forum tutorial aliases
        for source, target in COLLECTION_ALIASES["forum_tutorial"]:
            if product in source:
                product_aliases.append((source, target))

        # Add generic alias for the specific product (dynamic)
        generic_source = f"generic_{product}_{{tag}}"
        generic_target = f"generic_{product}_prod"
        product_aliases.append((generic_source, generic_target))

        if product_aliases:
            update_alias_pairs(client, product_aliases, tag)
            logger.info(f"Alias updates completed successfully for product: {product}")
        else:
            logger.warning(f"No alias configurations found for product: {product}")
    except Exception as e:
        logger.error(
            f"Failed to complete alias updates for product {product}: {str(e)}"
        )
        raise
