import os
import json
import datetime
import logging
import threading
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Type

from etlapp.common.config import app_config
from etlapp.common.context import EtlContext
from etlapp.common.file import (
    ensure_folder_exists,
    get_file_names_in_directory,
    read_text_from_file,
)
from etlapp.common.log import setup_logging
from etlapp.etl.flow import (
    etl_doc_embedding_flow,
    etl_doc_full_flow,
    etl_forum_qa_embedding_flow,
    etl_forum_tutorial_embedding_flow,
    etl_generic_full_flow,
    etl_generic_embedding_flow,
)

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Configuration for document processing."""

    root_path: str
    product: str
    parallel_count: int
    mode: str = "none"


class BaseDocumentProcessor:
    """Base class for document processors."""

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.context = EtlContext(config.root_path, self.doc_type, config.product, "0")

    @property
    def doc_type(self) -> str:
        """Get the document type."""
        raise NotImplementedError

    def get_processing_function(self) -> Callable[[EtlContext], None]:
        """Get the processing function to use."""
        raise NotImplementedError

    def get_file_list(self) -> List[str]:
        """Get the list of files to process."""
        raise NotImplementedError

    def process(self) -> None:
        """Process the documents."""
        file_list = self.get_file_list()
        logger.info(f"Found {len(file_list)} files to process for {self.doc_type}")

        if not file_list:
            return

        self._process_files(file_list)

    def _process_files(self, file_list: List[str]) -> None:
        """Process files using parallel threading."""
        split_list = self._split_list(file_list, self.config.parallel_count)
        threads = []

        for sub_list in split_list:
            thread = threading.Thread(target=self._process_sublist, args=(sub_list,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def _process_sublist(self, file_list: List[str]) -> None:
        """Process a sublist of files."""
        for file_name in file_list:
            try:
                context = EtlContext(
                    self.config.root_path,
                    self.doc_type,
                    self.config.product,
                    file_name,
                    self.context.thread_dict,
                )
                self.get_processing_function()(context)
            except Exception as e:
                logger.error(f"Error processing {file_name}: {str(e)}")
                continue

    @staticmethod
    def _split_list(lst: List[Any], n: int) -> List[List[Any]]:
        """Split a list into n roughly equal parts."""
        k, m = divmod(len(lst), n)
        return [lst[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n)]


class DocProcessor(BaseDocumentProcessor):
    """Processor for documentation files."""

    @property
    def doc_type(self) -> str:
        return "doc"

    def get_source_path(self) -> Path:
        if self.config.mode == "full":
            return (
                Path(self.config.root_path)
                / f"etl_doc/.temp/outputs_generate_qa/{self.config.product}"
            )
        return Path(self.config.root_path) / f"das/.temp/doc/{self.config.product}"

    def get_target_path(self) -> Path:
        if self.config.mode == "full":
            return (
                Path(self.config.root_path)
                / f"etl_doc/.temp/outputs_generate_qa_full/{self.config.product}"
            )
        return (
            Path(self.config.root_path)
            / f"etl_doc/.temp/outputs_embedding/{self.config.product}"
        )

    def get_file_list(self) -> List[str]:
        """Get the list of files to process."""
        source_path = self.get_source_path()
        target_path = self.get_target_path()

        ensure_folder_exists(str(source_path))
        ensure_folder_exists(str(target_path))

        source_files = get_file_names_in_directory(str(source_path))
        target_files = get_file_names_in_directory(str(target_path))

        source_files_names = [
            os.path.splitext(os.path.basename(f))[0] for f in source_files
        ]
        target_files_names = [
            os.path.splitext(os.path.basename(f))[0] for f in target_files
        ]

        if self.config.mode == "full":
            target_files_names = list(
                {"_".join(item.split("_")[:-2]) for item in target_files_names}
            )

        return list(set(source_files_names) - set(target_files_names))

    def get_processing_function(self) -> Callable[[EtlContext], None]:
        return (
            etl_doc_full_flow if self.config.mode == "full" else etl_doc_embedding_flow
        )


class ForumQAProcessor(BaseDocumentProcessor):
    """Processor for forum Q&A files."""

    @property
    def doc_type(self) -> str:
        return "forum/qa"

    def get_source_path(self) -> Path:
        return Path(self.config.root_path) / f"das/.temp/forum/qa/{self.config.product}"

    def get_target_path(self) -> Path:
        return (
            Path(self.config.root_path)
            / f"etl_forum_qa/.temp/outputs_embedding/{self.config.product}"
        )

    def get_processing_function(self) -> Callable[[EtlContext], None]:
        return etl_forum_qa_embedding_flow

    def get_file_list(self) -> List[str]:
        source_path = self.get_source_path()
        target_path = self.get_target_path()

        ensure_folder_exists(str(source_path))
        ensure_folder_exists(str(target_path))

        file_path = source_path / "combined.json"
        target_files = get_file_names_in_directory(str(target_path))

        file_content = read_text_from_file(str(file_path))
        thread_list_raw = json.loads(file_content)["threads"]
        logger.info(f"Found {len(thread_list_raw)} raw forum Q&A files")

        thread_dict = {}
        for thread in thread_list_raw:
            thread_dict[f"{thread['tid']}_{thread['postDate']}"] = thread

        min_date_time = self._get_timestamp("2021-01-01 00:00:00")
        max_date_time = (
            datetime.datetime.now() - datetime.timedelta(days=7)
        ).timestamp()

        threadlist_actual = [
            thread
            for thread in thread_list_raw
            if thread["postDate"] >= min_date_time
            and thread["postDate"] <= max_date_time
        ]

        logger.info(f"Filtered to {len(threadlist_actual)} forum Q&A files to process")

        source_files_names = [
            f"{thread['tid']}_{thread['postDate']}" for thread in threadlist_actual
        ]
        target_files_names = [os.path.basename(f).split(".")[0] for f in target_files]

        self.context.thread_dict = thread_dict
        return list(set(source_files_names) - set(target_files_names))

    @staticmethod
    def _get_timestamp(date_string: str) -> float:
        """Convert date string to timestamp."""
        date_format = "%Y-%m-%d %H:%M:%S"
        dt_object = datetime.datetime.strptime(date_string, date_format)
        return dt_object.timestamp()


class ForumTutorialProcessor(BaseDocumentProcessor):
    """Processor for forum tutorial files."""

    @property
    def doc_type(self) -> str:
        return "forum/tutorial"

    def get_source_path(self) -> Path:
        return (
            Path(self.config.root_path)
            / f"das/.temp/forum/tutorial/{self.config.product}"
        )

    def get_target_path(self) -> Path:
        return (
            Path(self.config.root_path)
            / f"etl_forum_tutorial/.temp/outputs_embedding/{self.config.product}"
        )

    def get_processing_function(self) -> Callable[[EtlContext], None]:
        return etl_forum_tutorial_embedding_flow

    def get_file_list(self) -> List[str]:
        source_path = self.get_source_path()
        target_path = self.get_target_path()

        ensure_folder_exists(str(source_path))
        ensure_folder_exists(str(target_path))

        file_path = source_path / "combined.json"
        target_files = get_file_names_in_directory(str(target_path))

        file_content = read_text_from_file(str(file_path))
        thread_list_raw = json.loads(file_content)["threads"]
        logger.info(f"Found {len(thread_list_raw)} raw forum tutorial files")

        thread_dict = {}
        for thread in thread_list_raw:
            thread_dict[f"{thread['tid']}_{thread['postDate']}"] = thread

        min_date_time = self._get_timestamp("2000-01-01 00:00:00")
        threadlist_actual = [
            thread for thread in thread_list_raw if thread["postDate"] >= min_date_time
        ]

        logger.info(
            f"Filtered to {len(threadlist_actual)} forum tutorial files to process"
        )

        source_files_names = [
            f"{thread['tid']}_{thread['postDate']}" for thread in threadlist_actual
        ]
        target_files_names = [os.path.basename(f).split(".")[0] for f in target_files]

        self.context.thread_dict = thread_dict
        return list(set(source_files_names) - set(target_files_names))

    @staticmethod
    def _get_timestamp(date_string: str) -> float:
        """Convert date string to timestamp."""
        date_format = "%Y-%m-%d %H:%M:%S"
        dt_object = datetime.datetime.strptime(date_string, date_format)
        return dt_object.timestamp()


class GenericProcessor(BaseDocumentProcessor):
    @property
    def doc_type(self) -> str:
        return "generic"

    def get_source_path(self) -> Path:
        if self.config.mode == "full":
            return (
                Path(self.config.root_path)
                / f"etl_generic/.temp/outputs_generate_qa/{self.config.product}"
            )
        return (
            Path(self.config.root_path)
            / f"das/.temp/generic_output/{self.config.product}"
        )

    def get_target_path(self) -> Path:
        if self.config.mode == "full":
            return (
                Path(self.config.root_path)
                / f"etl_generic/.temp/outputs_generate_qa_full/{self.config.product}"
            )
        return (
            Path(self.config.root_path)
            / f"etl_generic/.temp/outputs_embedding/{self.config.product}"
        )

    def get_file_list(self) -> List[str]:
        """Get the list of files to process."""
        source_path = self.get_source_path()
        target_path = self.get_target_path()

        ensure_folder_exists(str(source_path))
        ensure_folder_exists(str(target_path))

        source_files = get_file_names_in_directory(str(source_path))
        target_files = get_file_names_in_directory(str(target_path))

        source_files_names = [
            os.path.splitext(os.path.basename(f))[0] for f in source_files
        ]
        target_files_names = [
            os.path.splitext(os.path.basename(f))[0] for f in target_files
        ]

        if self.config.mode == "full":
            target_files_names = list(
                {"_".join(item.split("_")[:-2]) for item in target_files_names}
            )

        return list(set(source_files_names) - set(target_files_names))

    def get_processing_function(self) -> Callable[[EtlContext], None]:
        return (
            etl_generic_full_flow
            if self.config.mode == "full"
            else etl_generic_embedding_flow
        )


def get_processor(
    doc_type: str, config: ProcessingConfig
) -> Optional[BaseDocumentProcessor]:
    """Get the appropriate processor for the given document type."""
    processors: Dict[str, Type[BaseDocumentProcessor]] = {
        "doc": DocProcessor,
        "forum/qa": ForumQAProcessor,
        "forum/tutorial": ForumTutorialProcessor,
        "generic": GenericProcessor,
    }

    processor_class = processors.get(doc_type)
    if not processor_class:
        logger.error(f"Unknown document type: {doc_type}")
        return None

    return processor_class(config)


def etl_index_start(
    doc_type: str, product: str, mode: str, parallel_count: int
) -> None:
    """Start the ETL process for the given document type and product."""
    logger.info(f"Starting ETL process for {doc_type} - {product}")

    config = ProcessingConfig(
        root_path=app_config.root_path,
        product=product,
        parallel_count=parallel_count,
        mode=mode,
    )

    processor = get_processor(doc_type, config)
    if processor:
        processor.process()


def main():
    parser = argparse.ArgumentParser(description="ETL Index Entry Point")
    parser.add_argument(
        "--doc_type",
        type=str,
        default="generic",
        help="Document type (doc, forum/qa, forum/tutorial, generic)",
    )
    parser.add_argument(
        "--product",
        type=str,
        default="",
        help="Product name (forguncy, wyn, spreadjs, gcexcel, etc.)",
    )
    parser.add_argument("--mode", type=str, default="none", help="Mode (none, full)")
    parser.add_argument(
        "--parallel_count", type=int, default=1, help="Number of concurrent executions"
    )
    parser.add_argument(
        "--all", action="store_true", help="Process all types and products in batch"
    )
    args = parser.parse_args()

    if args.all:
        parallel_count = args.parallel_count

        # Process documentation
        for product in ["forguncy", "wyn", "spreadjs", "gcexcel"]:
            etl_index_start("doc", product, "none", parallel_count)
            etl_index_start("doc", product, "full", parallel_count)

        # Process forum Q&A
        for product in ["forguncy", "wyn", "spreadjsgcexcel"]:
            etl_index_start("forum/qa", product, "none", parallel_count)

        # Process forum tutorials
        for product in ["forguncy", "wyn", "spreadjsgcexcel"]:
            etl_index_start("forum/tutorial", product, "none", parallel_count)

        # Process generic documentation
        etl_index_start("generic", "", "none", parallel_count)
    else:
        etl_index_start(args.doc_type, args.product, args.mode, args.parallel_count)


if __name__ == "__main__":
    main()
