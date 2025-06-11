from typing import List, Dict
from qdrant_client import QdrantClient
import logging

from ragapp.common.config import app_config

# Initialize logger
logger = logging.getLogger(__name__)

# Fixed product configuration
FIXED_PRODUCTS = {
    "forguncy": {
        "id": "forguncy",
        "name": "Forguncy",
        "display_name": "ProductName.Forguncy",
    },
    "wyn": {"id": "wyn", "name": "Wyn", "display_name": "ProductName.Wyn"},
    "spreadjs": {
        "id": "spreadjs",
        "name": "SpreadJS",
        "display_name": "ProductName.SpreadJS",
    },
    "gcexcel": {
        "id": "gcexcel",
        "name": "GcExcel",
        "display_name": "ProductName.GcExcel",
    },
}


def get_generic_products() -> List[Dict]:
    """
    Get dynamic product list in generic mode
    This can be obtained from database, configuration files or other data sources
    """
    try:
        # Initialize vector database client
        url = app_config.vector_db.host
        client = QdrantClient(url)

        # Get all collections
        response = client.get_aliases()

        # Extract generic products
        generic_products = []
        for alia in response.aliases:
            if alia.alias_name.startswith("generic_") and alia.alias_name.endswith(
                "_prod"
            ):
                # Extract product ID from collection name: generic_productname_prod -> productname
                product_id = alia.alias_name[
                    8:-5
                ]  # Remove 'generic_' prefix and '_prod' suffix

                generic_products.append(
                    {
                        "id": product_id,
                        "name": product_id.title(),  # Capitalize first letter
                        "display_name": f"ProductName.{product_id.title()}",
                        "type": "generic",
                    }
                )

        return generic_products

    except Exception as e:
        logger.error(f"Error getting generic products: {e}")
        return []


def get_available_products(mode: str = "fixed") -> Dict:
    """
    Get available product list

    Args:
        mode: "fixed" for fixed product mode, "generic" for dynamic product mode

    Returns:
        Dictionary containing product list and mode information
    """
    try:
        if mode == "generic":
            products = get_generic_products()
            return {"mode": "generic", "products": products}
        else:
            # Fixed product mode
            products = [
                {
                    "id": product_id,
                    "name": product_info["name"],
                    "display_name": product_info["display_name"],
                    "type": "fixed",
                }
                for product_id, product_info in FIXED_PRODUCTS.items()
            ]

            return {"mode": "fixed", "products": products}

    except Exception as e:
        logger.error(f"Error getting available products: {e}")
        # Return fixed product list when error occurs
        products = [
            {
                "id": product_id,
                "name": product_info["name"],
                "display_name": product_info["display_name"],
                "type": "fixed",
            }
            for product_id, product_info in FIXED_PRODUCTS.items()
        ]

        return {"mode": "fixed", "products": products}
