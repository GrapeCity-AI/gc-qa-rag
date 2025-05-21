import requests
import logging
from typing import List, Dict


class KnowledgeBaseClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def search(self, keyword: str, product: str = None) -> List[Dict]:
        """Query the vector knowledge base"""
        url = f"{self.base_url}/search/"
        payload = {"keyword": keyword}
        if product:
            payload["product"] = product
            payload["mode"] = "chat"
        self.logger.debug(
            f"Querying knowledge base: keyword={keyword}, product={product}"
        )
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            hits = response.json()
            self.logger.debug(f"Knowledge base returned {len(hits)} results")
            return hits
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Knowledge base query failed: {e}")
            return []
