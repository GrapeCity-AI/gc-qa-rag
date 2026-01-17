"""
Forum API Connector - Connector for crawling forum content via API.

Fetches forum threads (QA or Tutorial) from a forum API service.
"""

import json
import logging
import re
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional

import requests

from ai_knowledge_service.abstractions.pipelines.source import (
    ConnectionResult,
    ISourceConnector,
    SourceConfig,
    SourceRecord,
)


class ForumProductType(Enum):
    """Supported forum product types."""
    FORGUNCY = "Forguncy"
    WYN = "Wyn"
    SPREADJS_GCEXCEL = "SpreadJSGcExcel"


class ForumSectionType(Enum):
    """Forum section types."""
    QA = "QA"
    TUTORIAL = "Tutorial"


class ForumApiConnector(ISourceConnector):
    """
    Forum API Connector - Fetches forum content via API.

    Supports:
    - Paginated thread listing
    - Thread content fetching
    - QA and Tutorial section types
    - Rate limiting and retry logic
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the connector.

        Args:
            logger: Optional logger instance.
        """
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._config: Optional[SourceConfig] = None
        self._base_url_page: str = ""
        self._base_url_thread: str = ""
        self._token: str = ""
        self._product: str = ""
        self._section: str = ""
        self._page_size: int = 50
        self._max_retries: int = 5
        self._retry_delay: float = 1.0
        self._request_delay: float = 0.1
        self._max_records: Optional[int] = None
        self._session: Optional[requests.Session] = None
        self._total_threads: int = 0

    @property
    def source_type(self) -> str:
        """Get the source type identifier."""
        return "forum_api"

    def configure(self, config: SourceConfig) -> None:
        """
        Configure the connector.

        Expected connection_params:
        - base_url_page: str - URL for page listing API
        - base_url_thread: str - URL for thread content API
        - token: str - API authentication token
        - product: str - Product name (Forguncy, Wyn, SpreadJSGcExcel)
        - section: str - Section type (QA, Tutorial)

        Expected fetch_options:
        - page_size: int - Threads per page (default: 50)
        - max_retries: int - Max retry attempts (default: 5)
        - retry_delay: float - Delay between retries (default: 1.0)
        - request_delay: float - Delay between requests (default: 0.1)
        - max_records: int - Max number of records to fetch (default: None = all)
        """
        if config.connector_type != self.source_type:
            raise ValueError(
                f"Invalid connector type: {config.connector_type}, "
                f"expected: {self.source_type}"
            )

        self._base_url_page = config.get_connection_param("base_url_page")
        self._base_url_thread = config.get_connection_param("base_url_thread")
        self._token = config.get_connection_param("token")
        self._product = config.get_connection_param("product")
        self._section = config.get_connection_param("section")

        if not all([self._base_url_page, self._base_url_thread, self._token]):
            raise ValueError(
                "Connection parameters 'base_url_page', 'base_url_thread', "
                "and 'token' are required"
            )

        if not self._product or not self._section:
            raise ValueError(
                "Connection parameters 'product' and 'section' are required"
            )

        self._page_size = config.get_fetch_option("page_size", 50)
        self._max_retries = config.get_fetch_option("max_retries", 5)
        self._retry_delay = config.get_fetch_option("retry_delay", 1.0)
        self._request_delay = config.get_fetch_option("request_delay", 0.1)
        self._max_records = config.get_fetch_option("max_records", None)

        self._config = config

        self._logger.info(
            f"Configured forum connector: product={self._product}, "
            f"section={self._section}"
        )

    def validate_connection(self) -> ConnectionResult:
        """Validate that the forum API is accessible."""
        if not self._base_url_page:
            return ConnectionResult.error("Connector not configured")

        try:
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 Chrome/91.0.4472.124 Safari/537.36"
            })

            # Test connection with first page
            url = self._build_page_url(1)
            response = self._session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if "tidList" not in data:
                return ConnectionResult.error(
                    "Invalid API response: missing 'tidList'",
                    product=self._product,
                    section=self._section,
                )

            return ConnectionResult.success(
                f"Connected to forum API: {self._product}/{self._section}"
            )

        except requests.RequestException as e:
            return ConnectionResult.error(
                f"Failed to connect to forum API: {e}",
                product=self._product,
                section=self._section,
            )
        except json.JSONDecodeError as e:
            return ConnectionResult.error(
                f"Invalid JSON response: {e}",
                product=self._product,
                section=self._section,
            )

    def fetch(self) -> Iterator[SourceRecord]:
        """Fetch all threads from the forum."""
        if not self._base_url_page:
            raise ConnectionError("Connector not configured")

        validation = self.validate_connection()
        if not validation.is_connected:
            raise ConnectionError(validation.message)

        self._logger.info(
            f"Starting fetch from forum: {self._product}/{self._section}"
            + (f" (limit: {self._max_records})" if self._max_records else "")
        )

        page = 1
        self._total_threads = 0

        while True:
            # Check limit
            if self._max_records is not None and self._total_threads >= self._max_records:
                self._logger.info(f"Reached max_records limit ({self._max_records})")
                break

            # Fetch page listing
            page_data = self._fetch_page(page)
            if not page_data:
                break

            threads = page_data.get("tidList", [])
            if not threads:
                break

            # Fetch each thread's content
            for thread in threads:
                # Check limit
                if self._max_records is not None and self._total_threads >= self._max_records:
                    break

                record = self._fetch_thread(thread)
                if record is not None:
                    yield record
                    self._total_threads += 1

                if self._request_delay > 0:
                    time.sleep(self._request_delay)

            # Check for next page
            if not page_data.get("nextLink"):
                break

            page += 1

        self._logger.info(f"Fetched {self._total_threads} threads total")

    def fetch_incremental(
        self,
        since: datetime,
    ) -> Iterator[SourceRecord]:
        """
        Incremental fetch is not fully supported.

        The forum API doesn't support filtering by date, so we fetch all
        and let the ingestion executor handle deduplication.
        """
        self._logger.warning(
            "Forum API connector does not fully support incremental fetch, "
            "fetching all threads"
        )
        yield from self.fetch()

    @property
    def supports_incremental(self) -> bool:
        """Check if this connector supports incremental fetching."""
        return False

    def get_record_count(self) -> Optional[int]:
        """Get the total number of threads (unknown without full scan)."""
        return None

    def _build_page_url(self, page: int) -> str:
        """Build URL for page listing API."""
        return (
            f"{self._base_url_page}?"
            f"token={self._token}&"
            f"product={self._product}&"
            f"type={self._section}&"
            f"page={page}"
        )

    def _build_thread_url(self, thread_id: str) -> str:
        """Build URL for thread content API."""
        return (
            f"{self._base_url_thread}?"
            f"token={self._token}&"
            f"product={self._product}&"
            f"type={self._section}&"
            f"tid={thread_id}"
        )

    def _fetch_page(self, page: int) -> Optional[Dict[str, Any]]:
        """Fetch a page of thread listings."""
        url = self._build_page_url(page)

        for attempt in range(self._max_retries):
            try:
                response = self._session.get(url, timeout=30)
                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                self._logger.warning(
                    f"Attempt {attempt + 1}/{self._max_retries} failed for page {page}: {e}"
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))

        self._logger.error(f"Failed to fetch page {page} after {self._max_retries} attempts")
        return None

    def _fetch_thread(self, thread: Dict[str, Any]) -> Optional[SourceRecord]:
        """Fetch a single thread's content."""
        thread_id = thread.get("tid")
        if not thread_id:
            return None

        # Fetch thread content
        url = self._build_thread_url(thread_id)

        for attempt in range(self._max_retries):
            try:
                response = self._session.get(url, timeout=30)
                response.raise_for_status()
                content_data = response.json()

                # Combine thread metadata with content
                thread["content"] = content_data

                # Clean HTML content (remove img tags)
                thread_json = json.dumps(thread, ensure_ascii=False)
                thread_json = self._remove_img_tags(thread_json)
                thread = json.loads(thread_json)

                # Create source record
                source_uri = f"{self._product}_{self._section}_{thread_id}"

                self._logger.debug(f"Fetched thread: {thread_id}")

                return SourceRecord(
                    source_uri=source_uri,
                    content=json.dumps(thread, ensure_ascii=False).encode("utf-8"),
                    content_type="application/json",
                    metadata={
                        "source_type": self.source_type,
                        "product": self._product,
                        "section": self._section,
                        "thread_id": thread_id,
                        "title": thread.get("title", ""),
                        "post_date": thread.get("postDate", ""),
                        "thread_data": thread,
                    },
                    fetched_at=datetime.now(),
                )

            except requests.RequestException as e:
                self._logger.warning(
                    f"Attempt {attempt + 1}/{self._max_retries} failed for thread {thread_id}: {e}"
                )
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay * (attempt + 1))
            except json.JSONDecodeError as e:
                self._logger.warning(f"Invalid JSON for thread {thread_id}: {e}")
                break

        self._logger.warning(
            f"Failed to fetch thread {thread_id} after {self._max_retries} attempts"
        )
        return None

    @staticmethod
    def _remove_img_tags(content: str) -> str:
        """Remove image tags from content."""
        if not content:
            return content
        return re.sub(r"<img.*?>", "", content)
