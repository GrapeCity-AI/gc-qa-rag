from typing import Literal
import logging
from dataclasses import dataclass
from etlapp.common.config import app_config
from etlapp.common.log import setup_logging
from etlapp.das.das_doc import crawl_doc, DocProductType
from etlapp.das.das_forum import ForumSectionType, ForumProductType, ForumCrawler
import argparse

from etlapp.das.das_generic import das_generic_main

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class CrawlerConfig:
    """Configuration for the crawler."""

    root_path: str
    doc_types: list[DocProductType] = (
        DocProductType.FORGUNCY,
        DocProductType.WYN,
        DocProductType.SPREADJS,
        DocProductType.GCEXCEL,
    )
    forum_products: list[ForumProductType] = (
        ForumProductType.FORGUNCY,
        ForumProductType.WYN,
        ForumProductType.SPREADJS_GCEXCEL,
    )


def crawl_all_doc(config: CrawlerConfig) -> None:
    """Crawl documentation for all configured product types."""
    try:
        for product_type in config.doc_types:
            logger.info(f"Crawling documentation for {product_type.name}")
            crawl_doc(config.root_path, product_type)
    except Exception as e:
        logger.error(f"Error crawling documentation: {str(e)}")
        raise


def crawl_all_forum(config: CrawlerConfig, section_type: ForumSectionType) -> None:
    """Crawl forum content for all configured products and specified section type."""
    try:
        crawler = ForumCrawler()
        for product in config.forum_products:
            logger.info(f"Crawling {section_type.value} forum for {product.value}")
            crawler.crawl_forum(config.root_path, product, section_type, 1)
    except Exception as e:
        logger.error(f"Error crawling {section_type.value} forum: {str(e)}")
        raise


def crawl_index_start(
    doc_type: Literal["doc", "forum/qa", "forum/tutorial", "generic"], product: str
) -> None:
    """Start crawling based on the specified document type."""
    try:
        logger.info(f"Starting crawl for document type: {doc_type}, product:{product}")

        config = CrawlerConfig(root_path=app_config.root_path)

        if doc_type == "doc":
            crawl_all_doc(config)
        elif doc_type == "forum/qa":
            crawl_all_forum(config, ForumSectionType.QA)
        elif doc_type == "forum/tutorial":
            crawl_all_forum(config, ForumSectionType.Tutorial)
        elif doc_type == "generic":
            das_generic_main(product)

        logger.info(f"Completed crawl for {doc_type}")
    except Exception as e:
        logger.error(f"Error in crawl_index_start: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Crawl documentation and forum content, convert generic files."
    )
    parser.add_argument(
        "--types",
        action="append",
        choices=["doc", "forum/qa", "forum/tutorial", "generic"],
        default=["generic"],
        help="Types to crawl: doc, forum/qa, forum/tutorial. If not specified, convert generic only.",
    )
    parser.add_argument(
        "--product",
        type=str,
        default="",
        help="Product name (forguncy, wyn, spreadjs, gcexcel, etc.)",
    )
    args = parser.parse_args()

    # If no types specified, convert generic only
    types_to_crawl = args.types if args.types else ["generic"]

    try:
        for doc_type in types_to_crawl:
            crawl_index_start(doc_type, args.product)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise
