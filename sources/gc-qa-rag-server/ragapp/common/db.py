from typing import Generator, List, Dict, Any
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    SmallInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging
from ragapp.common.config import app_config

# Initialize logger
logger = logging.getLogger(__name__)

Base = declarative_base()


class SearchHistory(Base):
    """Model for search history records."""

    __tablename__ = "SearchHistory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    mode = Column(String(32))
    product = Column(String(32))
    session_id = Column(String(36))
    session_index = Column(Integer)
    create_time = Column(DateTime, default=datetime.now)


class QAFeedback(Base):
    """Model for QA feedback records."""

    __tablename__ = "QAFeedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    rating = Column(SmallInteger)
    comments = Column(Text)
    product = Column(String(32))
    create_time = Column(DateTime, default=datetime.now)


class Database:
    """Database class to handle all database operations using SQLAlchemy."""

    def __init__(self):
        """Initialize database connection parameters."""
        try:
            self.engine = create_engine(app_config.db.connection_string)
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )

            # Create all tables
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            logger.exception("Initilized database failed", e)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions.

        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()

    def add_search_history(
        self, query: str, mode: str, product: str, session_id: str, session_index: int
    ) -> bool:
        """Add a search history record to the database.

        Args:
            query: The search query
            mode: The search mode
            product: The product name
            session_id: The session ID
            session_index: The session index

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                history = SearchHistory(
                    query=query,
                    mode=mode,
                    product=product,
                    session_id=session_id,
                    session_index=session_index,
                )
                session.add(history)
            return True
        except Exception as e:
            logger.error(f"Error occurred while inserting into SearchHistory: {e}")
            return False

    def add_qa_feedback(
        self, question: str, answer: str, rating: int, comments: str, product: str
    ) -> bool:
        """Add a QA feedback record to the database.

        Args:
            question: The question text
            answer: The answer text
            rating: The rating value
            comments: Additional comments
            product: The product name

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.get_session() as session:
                feedback = QAFeedback(
                    question=question,
                    answer=answer,
                    rating=rating,
                    comments=comments,
                    product=product,
                )
                session.add(feedback)
            return True
        except Exception as e:
            logger.error(f"Error occurred while inserting into QAFeedback: {e}")
            return False

    def get_search_history_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Get search history records for a specific date.

        Args:
            date: The date to query for

        Returns:
            List[Dict[str, Any]]: List of search history records
        """
        try:
            with self.get_session() as session:
                results = (
                    session.query(SearchHistory)
                    .filter(SearchHistory.create_time.cast(String).like(f"{date}%"))
                    .all()
                )
                return [
                    {
                        "id": r.id,
                        "query": r.query,
                        "mode": r.mode,
                        "product": r.product,
                        "session_id": r.session_id,
                        "session_index": r.session_index,
                        "create_time": r.create_time,
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Error occurred while querying SearchHistory: {e}")
            return []


# Create a global database instance
db = Database()
