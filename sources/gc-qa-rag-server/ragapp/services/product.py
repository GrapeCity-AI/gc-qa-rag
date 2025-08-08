from typing import List, Dict
import logging
import requests

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
        # Use HTTP request to get collections from vector database
        vector_db_url = app_config.vector_db.host
        if not vector_db_url.startswith('http'):
            vector_db_url = f"http://{vector_db_url}"

        collections_url = f"{vector_db_url}/collections"

        # Make HTTP request to get collections
        response = requests.get(collections_url, timeout=10)
        response.raise_for_status()

        collections_data = response.json()
        collections = collections_data.get("result", {}).get("collections", [])

        # Extract generic products from collection names
        generic_products = []
        seen_products = set()  # Track unique products

        for collection in collections:
            collection_name = collection.get("name", "")
            # Look for collections with pattern: generic_PRODUCT_YYYYMMDD
            if collection_name.startswith("generic_"):
                # Extract product name from collection name: generic_A_250813 -> A
                parts = collection_name.split("_")
                if len(parts) >= 3:  # generic_PRODUCT_TAG format
                    product_id = parts[1]  # Get the product part (e.g., "A")

                    # Only add each product once
                    if product_id not in seen_products:
                        seen_products.add(product_id)
                        generic_products.append(
                            {
                                "id": product_id,
                                "name": product_id.title(),  # Capitalize first letter
                                "display_name": f"ProductName.{product_id.title()}",
                                "type": "generic",
                            }
                        )

        logger.info(f"Found {len(generic_products)} generic products: {[p['id'] for p in generic_products]}")
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
