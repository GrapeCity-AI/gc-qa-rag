"""
Sitemap Connector - Connector for crawling documentation sites via sitemap.xml.

Fetches URLs from sitemap.xml and downloads HTML content for each page.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Iterator, List, Optional
from xml.etree import ElementTree

import requests

from ai_knowledge_service.abstractions.pipelines.source import (
    ConnectionResult,
    ISourceConnector,
    SourceConfig,
    SourceRecord,
)


class SitemapConnector(ISourceConnector):
    """
    Sitemap Connector - Crawls documentation sites via sitemap.xml.

    Supports:
    - Parsing sitemap.xml for URL list
    - HTTP fetching with retry
    - Rate limiting to avoid overloading servers
    - Metadata extraction (title, category from URL structure)
    """

    SITEMAP_NAMESPACE = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the connector.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Optional[SourceConfig] = None
        self._sitemap_url: str = ""
        self._product_name: str = ""
        self._request_delay: float = 0.1
        self._max_retries: int = 3
        self._retry_delay: float = 1.0
        self._max_records: Optional[int] = None
        self._session: Optional[requests.Session] = None
        self._urls: List[str] = []
        self._common_prefix: str = ""

    @property
    def source_type(self) -> str:
        """Get the source type identifier."""
        return "sitemap"

    def configure(self, config: SourceConfig) -> None:
        """
        Configure the connector.

        Expected connection_params:
        - sitemap_url: str - URL of the sitemap.xml
        - product_name: str - Name of the product (for metadata)

        Expected fetch_options:
        - request_delay: float - Delay between requests in seconds (default: 0.1)
        - max_retries: int - Max retry attempts (default: 3)
        - retry_delay: float - Delay between retries (default: 1.0)
        - max_records: int - Max number of records to fetch (default: None = all)
        """
        if config.connector_type != self.source_type:
            raise ValueError(
                f"Invalid connector type: {config.connector_type}, "
                f"expected: {self.source_type}"
            )

        self._sitemap_url = config.get_connection_param("sitemap_url")
        if not self._sitemap_url:
            raise ValueError("Connection parameter 'sitemap_url' is required")

        self._product_name = config.get_connection_param("product_name", "unknown")

        self._request_delay = config.get_fetch_option("request_delay", 0.1)
        self._max_retries = config.get_fetch_option("max_retries", 3)
        self._retry_delay = config.get_fetch_option("retry_delay", 1.0)
        self._max_records = config.get_fetch_option("max_records", None)

        self._config = config

        self._logger.info(
            f"Configured sitemap connector: url={self._sitemap_url}, "
            f"product={self._product_name}"
        )

    def validate_connection(self) -> ConnectionResult:
        """Validate that the sitemap is accessible and parse URLs."""
        if not self._sitemap_url:
            return ConnectionResult.error("Connector not configured")

        try:
            # Initialize session
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 Chrome/91.0.4472.124 Safari/537.36"
            })

            # Fetch and parse sitemap
            response = self._session.get(self._sitemap_url, timeout=30)
            response.raise_for_status()

            # Parse XML
            root = ElementTree.fromstring(response.content)
            self._urls = [
                loc.text
                for loc in root.findall(".//ns:loc", self.SITEMAP_NAMESPACE)
                if loc.text
            ]

            if not self._urls:
                return ConnectionResult.error(
                    "No URLs found in sitemap",
                    sitemap_url=self._sitemap_url,
                )

            # Find common prefix for URL path extraction
            self._common_prefix = self._find_common_prefix(self._urls)

            return ConnectionResult.success(
                f"Connected to sitemap, found {len(self._urls)} URLs"
            )

        except requests.RequestException as e:
            return ConnectionResult.error(
                f"Failed to fetch sitemap: {e}",
                sitemap_url=self._sitemap_url,
            )
        except ElementTree.ParseError as e:
            return ConnectionResult.error(
                f"Failed to parse sitemap XML: {e}",
                sitemap_url=self._sitemap_url,
            )

    def fetch(self) -> Iterator[SourceRecord]:
        """Fetch all pages from the sitemap."""
        if not self._sitemap_url:
            raise ConnectionError("Connector not configured")

        # Validate and parse sitemap if not done
        if not self._urls:
            validation = self.validate_connection()
            if not validation.is_connected:
                raise ConnectionError(validation.message)

        urls_to_fetch = self._urls
        if self._max_records is not None:
            urls_to_fetch = self._urls[:self._max_records]

        self._logger.info(f"Starting fetch of {len(urls_to_fetch)} URLs from sitemap")

        for index, url in enumerate(urls_to_fetch):
            try:
                record = self._fetch_page(url, index, len(urls_to_fetch))
                if record is not None:
                    yield record

                # Rate limiting
                if self._request_delay > 0:
                    time.sleep(self._request_delay)

            except Exception as e:
                self._logger.error(f"Error fetching {url}: {e}")
                continue

    def fetch_incremental(
        self,
        since: datetime,
    ) -> Iterator[SourceRecord]:
        """
        Incremental fetch is not supported for sitemap connector.

        Falls back to full fetch with a warning.
        """
        self._logger.warning(
            "Sitemap connector does not support incremental fetch, "
            "performing full fetch"
        )
        yield from self.fetch()

    @property
    def supports_incremental(self) -> bool:
        """Check if this connector supports incremental fetching."""
        return False

    def get_record_count(self) -> Optional[int]:
        """Get the total number of URLs in the sitemap."""
        if self._urls:
            return len(self._urls)

        # Try to validate and get count
        validation = self.validate_connection()
        if validation.is_connected:
            return len(self._urls)

        return None

    def _fetch_page(self, url: str, index: int, total: int) -> Optional[SourceRecord]:
        """
        Fetch a single page with retry logic.

        Args:
            url: URL to fetch.
            index: Index for logging progress.
            total: Total number of URLs to fetch.

        Returns:
            SourceRecord if successful, None otherwise.
        """
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 Chrome/91.0.4472.124 Safari/537.36"
            })

        for attempt in range(self._max_retries):
            try:
                response = self._session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"

                content = response.text
                content_bytes = content.encode("utf-8")

                # Extract metadata from URL
                source_uri = url.replace(self._common_prefix, "").replace("/", "_")
                if source_uri.startswith("_"):
                    source_uri = source_uri[1:]

                progress = (index + 1) / total * 100
                self._logger.info(f"[{progress:.1f}%] Fetched: {url}")

                return SourceRecord(
                    source_uri=source_uri,
                    content=content_bytes,
                    content_type="text/html",
                    metadata={
                        "source_type": self.source_type,
                        "url": url,
                        "product": self._product_name,
                        "content_html": content,
                    },
                    fetched_at=datetime.now(),
                )

            except requests.RequestException as e:
                self._logger.warning(
                    f"Attempt {attempt + 1}/{self._max_retries} failed for {url}: {e}"
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))

        self._logger.error(f"Failed to fetch {url} after {self._max_retries} attempts")
        return None

    @staticmethod
    def _find_common_prefix(strings: List[str]) -> str:
        """Find the longest common prefix among a list of strings."""
        if not strings:
            return ""

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""
        return prefix
