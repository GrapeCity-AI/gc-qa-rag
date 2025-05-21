from enum import Enum
import time
import requests
import json
import re
import os
import logging
from lxml import etree
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Dict, Optional, List

from etlapp.common.file import ensure_folder_exists, write_text_to_file
from etlapp.common.hash import get_hash_str

# Configure logging
logger = logging.getLogger(__name__)


class DocProductType(Enum):
    FORGUNCY = "Forguncy"
    WYN = "Wyn"
    SPREADJS = "SpreadJS"
    GCEXCEL = "GcExcel"


@dataclass
class ProductConfig:
    product_name: str
    sitemap_url: str
    save_sub_path: str

    @classmethod
    def get_product_configs(cls) -> Dict[DocProductType, "ProductConfig"]:
        return {
            DocProductType.FORGUNCY: cls(
                product_name="Forguncy",
                sitemap_url="https://www.grapecity.com.cn/solutions/huozige/help/docs/__sitemap.xml",
                save_sub_path="das/.temp/doc/forguncy/",
            ),
            DocProductType.WYN: cls(
                product_name="Wyn",
                sitemap_url="https://www.grapecity.com.cn/solutions/wyn/help/docs/__sitemap.xml",
                save_sub_path="das/.temp/doc/wyn/",
            ),
            DocProductType.SPREADJS: cls(
                product_name="SpreadJS",
                sitemap_url="https://demo.grapecity.com.cn/spreadjs/help/docs/__sitemap.xml",
                save_sub_path="das/.temp/doc/spreadjs/",
            ),
            DocProductType.GCEXCEL: cls(
                product_name="GcExcel",
                sitemap_url="https://www.grapecity.com.cn/developer/grapecitydocuments/excel-java/docs/__sitemap.xml",
                save_sub_path="das/.temp/doc/gcexcel/",
            ),
        }


class HttpClient:
    def __init__(self, retry_count: int = 3, retry_delay: int = 1):
        self.headers = {
            "User-Agent": "Chrome/91.0.4472.124 Safari/537.36",
        }
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def get(self, url: str) -> Optional[str]:
        """Fetch content from URL with retry mechanism."""
        for attempt in range(self.retry_count):
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    response.encoding = response.apparent_encoding
                    return response.text
                else:
                    logger.error(
                        f"Failed to fetch URL {url}, status code: {response.status_code}"
                    )
            except Exception as e:
                logger.error(
                    f"Error fetching URL {url} (attempt {attempt + 1}): {str(e)}"
                )
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
        return None


class SitemapParser:
    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def parse(self, sitemap_url: str) -> List[str]:
        """Parse sitemap and return list of URLs."""
        sitemap_content = self.http_client.get(sitemap_url)
        if not sitemap_content:
            logger.error(f"Failed to fetch sitemap from {sitemap_url}")
            return []

        try:
            root = etree.fromstring(sitemap_content.encode("utf-8"), etree.XMLParser())
            urls = [
                url.text
                for url in root.xpath(
                    "//ns:loc",
                    namespaces={"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"},
                )
            ]
            return urls
        except Exception as e:
            logger.error(f"Error parsing sitemap: {str(e)}")
            return []

    @staticmethod
    def find_common_prefix(strings: List[str]) -> str:
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


class HtmlExtractor:
    @staticmethod
    def get_title(content: str) -> str:
        """Extract title from HTML content."""
        try:
            soup = BeautifulSoup(content, "html.parser")
            element = soup.find(id="site_main_content-doc-content_title")
            return element.text if element else ""
        except Exception as e:
            logger.error(f"Error extracting title: {str(e)}")
            return ""

    @staticmethod
    def get_category(content: str) -> str:
        """Extract category from HTML content."""
        try:
            soup = BeautifulSoup(content, "html.parser")
            element = soup.find(class_="nav__breadcrumb-items")
            if element:
                single = HtmlExtractor.replace_consecutive_newlines(element.text).strip(
                    "/"
                )
                if "/" in single:
                    single = single.rsplit("/", 1)[0]
                return single
            return ""
        except Exception as e:
            logger.error(f"Error extracting category: {str(e)}")
            return ""

    @staticmethod
    def replace_consecutive_newlines(s: str) -> str:
        """Replace consecutive newlines with a single forward slash."""
        return re.sub(r"\n+", "/", s)


class FileSaver:
    def __init__(self, save_delay: float = 0.1):
        self.save_delay = save_delay

    def save_doc(self, product: str, url: str, content: str, save_path: str) -> None:
        """Save document content to file."""
        try:
            content_hash = get_hash_str(content)
            title = HtmlExtractor.get_title(content)
            category = HtmlExtractor.get_category(content)

            doc_object = {
                "product": product,
                "url": url,
                "title": title,
                "category": category,
                "content_html": content,
                "content_hash": content_hash,
            }

            save_file_content = json.dumps(doc_object, ensure_ascii=False)
            save_file_path = f"{save_path}_{content_hash[:12]}.json"
            write_text_to_file(save_file_path, save_file_content)
            time.sleep(self.save_delay)
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")


class DocCrawler:
    def __init__(self):
        self.http_client = HttpClient()
        self.sitemap_parser = SitemapParser(self.http_client)
        self.file_saver = FileSaver()

    def crawl(self, product: str, sitemap_url: str, save_path: str) -> None:
        """Crawl documentation from a sitemap URL and save to specified path."""
        try:
            urls = self.sitemap_parser.parse(sitemap_url)
            if not urls:
                logger.error(f"No URLs found in sitemap for {product}")
                return

            logger.info(f"Start crawling sitemap's URL...{len(urls)}")
            array_length = len(urls)
            common_prefix = self.sitemap_parser.find_common_prefix(urls)

            for index, url in enumerate(urls):
                try:
                    file_name = url.replace(common_prefix, "").replace("/", "_")
                    content = self.http_client.get(url)
                    if content:
                        self.file_saver.save_doc(
                            product, url, content, f"{save_path}{file_name}"
                        )
                    progress_percentage = (index + 1) / array_length * 100
                    logger.info(f"Progress: {progress_percentage:.2f}%")
                except Exception as e:
                    logger.error(f"Error processing URL {url}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error during crawling for {product}: {str(e)}")


def crawl_doc(root_path: str, product_type: DocProductType) -> None:
    """
    Crawl documentation for a specific product type.

    Args:
        root_path: Root directory path for saving files
        product_type: Type of product to crawl
    """
    try:
        # Get product configuration
        products = ProductConfig.get_product_configs()
        if product_type not in products:
            logger.error(f"Invalid product type: {product_type}")
            return

        product = products[product_type]
        save_path = os.path.join(root_path, product.save_sub_path)

        # Ensure save directory exists
        ensure_folder_exists(save_path)

        # Initialize and run crawler
        crawler = DocCrawler()
        crawler.crawl(product.product_name, product.sitemap_url, save_path)

    except Exception as e:
        logger.error(f"Error in crawl_doc for {product_type}: {str(e)}")
        raise
