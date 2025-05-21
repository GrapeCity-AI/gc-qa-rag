from enum import Enum
import re
import time
import logging
import requests
import json
from dataclasses import dataclass
from typing import Dict, Optional, Any
from pathlib import Path
from etlapp.common.config import app_config
from etlapp.common.file import (
    ensure_folder_exists,
    read_text_from_file,
    write_text_to_file,
)

# Configure logging
logger = logging.getLogger(__name__)


class ForumProductType(Enum):
    FORGUNCY = "Forguncy"
    WYN = "Wyn"
    SPREADJS_GCEXCEL = "SpreadJSGcExcel"


class ForumSectionType(Enum):
    QA = "QA"
    Tutorial = "Tutorial"


@dataclass
class CrawlerConfig:
    base_url_page: str = app_config.das.base_url_page
    base_url_thread: str = app_config.das.base_url_thread
    token: str = app_config.das.token
    max_retries: int = 5
    retry_delay: int = 1
    page_size: int = 50


class HttpClient:
    def __init__(self, max_retries: int = 5, retry_delay: int = 1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session = requests.Session()
        self._session.headers.update(
            {"User-Agent": "Chrome/91.0.4472.124 Safari/537.36"}
        )
        self.base_url_page = ""
        self.base_url_thread = ""
        self.token = ""

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from URL with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                response = self._session.get(url)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(
                        f"Failed to fetch {url} after {self.max_retries} attempts"
                    )
                    return None

    def fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch and parse JSON content from URL."""
        content = self.fetch_url(url)
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from {url}")
            return {}


class ForumCrawler:
    def __init__(self, config: CrawlerConfig = CrawlerConfig()):
        self.config = config
        self.http_client = HttpClient(config.max_retries, config.retry_delay)
        self.http_client.base_url_page = config.base_url_page
        self.http_client.base_url_thread = config.base_url_thread
        self.http_client.token = config.token
        self.file_manager = None
        self.thread_processor = None

    def crawl_forum(
        self,
        root_path: str,
        product: ForumProductType,
        section: ForumSectionType,
        start_page: int,
    ) -> None:
        """Crawl forum content starting from specified page."""
        self.file_manager = FileManager(root_path)
        self.thread_processor = ThreadProcessor(self.http_client, self.file_manager)

        folder = self.file_manager.get_section_folder(section, product)
        stack = [(start_page, product, section)]

        while stack:
            page, product, section = stack.pop()
            target_file = folder / f"{product.value}_{section.value}_{page}.json"

            # Load existing page if available
            page_data = self.file_manager.read_json_file(target_file)

            # Process threads
            if (
                page_data
                and len(page_data.get("tidList", [])) == self.config.page_size
                and page_data.get("nextLink")
            ):
                threads = [
                    t
                    for t in page_data["tidList"]
                    if not t.get("content") or not t["content"].get("authorContent")
                ]
                if threads:
                    logger.info(
                        f"{target_file} exists, {len(threads)} threads need updating"
                    )
            else:
                page_data = self.http_client.fetch_json(
                    f"{self.config.base_url_page}?token={self.config.token}&product={product.value}&type={section.value}&page={page}"
                )
                threads = page_data.get("tidList", [])

            # Update thread content
            if threads:
                page_data = self.thread_processor.process_page(
                    page_data, product, section
                )
                self.file_manager.write_json_file(target_file, page_data)
                logger.info(f"Saved {target_file}")

            # Process next page
            if page_data.get("nextLink"):
                stack.append((page + 1, product, section))
            else:
                self.file_manager.merge_thread_files(folder)


class FileManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self._ensure_base_folders()

    def _ensure_base_folders(self):
        """Ensure all necessary base folders exist."""
        ensure_folder_exists(str(self.root_path))

    def get_section_folder(
        self, section: ForumSectionType, product: ForumProductType
    ) -> Path:
        """Get the folder path for a specific section and product."""
        folder = (
            self.root_path
            / "das/.temp/forum"
            / section.value.lower()
            / product.value.lower()
        )
        ensure_folder_exists(str(folder))
        return folder

    def read_json_file(self, file_path: Path) -> Dict[str, Any]:
        """Read and parse JSON content from file."""
        if not file_path.exists():
            logger.info(f"File does not exist: {file_path}")
            return {}
        try:
            content = read_text_from_file(str(file_path))
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error reading {file_path}: {str(e)}")
            return {}

    def write_json_file(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write JSON data to file."""
        try:
            write_text_to_file(str(file_path), json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Error writing to {file_path}: {str(e)}")

    def merge_thread_files(self, folder: Path) -> None:
        """Merge all thread files into a single combined file."""
        merged_file = folder / "combined.json"
        if merged_file.exists():
            merged_file.unlink()

        all_threads = []
        for file in folder.glob("*.json"):
            if file.name == "combined.json":
                continue
            try:
                content = read_text_from_file(str(file))
                content = self._replace_img_to_empty(content)
                threads = json.loads(content)["tidList"]
                all_threads.extend(threads)
            except Exception as e:
                logger.error(f"Error processing {file}: {str(e)}")

        all_threads.sort(key=lambda x: x["postDate"])
        self.write_json_file(merged_file, {"threads": all_threads})
        logger.info(f"Merged {len(all_threads)} threads into {merged_file}")

    @staticmethod
    def _replace_img_to_empty(content: str) -> str:
        """Remove image tags from content."""
        if not content:
            return content
        return re.sub(r"<img.*?>", "", content)


class ThreadProcessor:
    def __init__(self, http_client: HttpClient, file_manager: FileManager):
        self.http_client = http_client
        self.file_manager = file_manager
        self.total_count = 0
        self.failed_count = 0

    def process_thread(
        self,
        thread: Dict[str, Any],
        product: ForumProductType,
        section: ForumSectionType,
    ) -> Dict[str, Any]:
        """Process a single thread and update its content."""
        thread_id = thread["tid"]
        thread_content = self.http_client.fetch_json(
            f"{self.http_client.base_url_thread}?token={self.http_client.token}&product={product.value}&type={section.value}&tid={thread_id}"
        )
        thread["content"] = thread_content

        self.total_count += 1
        if not thread_content or not thread_content.get("authorContent"):
            self.failed_count += 1

        logger.info(
            f"Processed thread {thread_id} (Total: {self.total_count}, Failed: {self.failed_count})"
        )
        return thread

    def process_page(
        self,
        page_data: Dict[str, Any],
        product: ForumProductType,
        section: ForumSectionType,
    ) -> Dict[str, Any]:
        """Process all threads in a page."""
        threads = page_data.get("tidList", [])
        for thread in threads:
            thread = self.process_thread(thread, product, section)
        return page_data
