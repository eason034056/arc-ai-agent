"""
Database Connection Module

This module manages database connections and sessions using SQLAlchemy.

Key Concepts:
- Engine: Low-level database connection pool
- SessionLocal: Factory for creating database sessions
- Base: Base class for all ORM models
- get_db(): Dependency injection function for FastAPI

Usage in FastAPI:
    from app.db.connection import get_db
    
    @app.get("/batches")
    def list_batches(db: Session = Depends(get_db)):
        return db.query(PayrollBatch).all()
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import get_settings
from app.core.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)

# Get application settings
settings = get_settings()

# ========================================
# DATABASE ENGINE
# ========================================
# The engine manages connections to the database
# It maintains a connection pool for efficiency
engine = create_engine(
    settings.database_url,
    
    # pool_pre_ping: Check connection health before using
    # This prevents "connection lost" errors
    pool_pre_ping=True,
    
    # pool_size: Number of connections to keep in the pool
    # Adjust based on your application's concurrency needs
    pool_size=10,
    
    # max_overflow: Additional connections beyond pool_size
    # Total connections = pool_size + max_overflow
    max_overflow=20,
    
    # echo: Log all SQL statements (useful for debugging)
    # Set to False in production for performance
    echo=settings.is_dev,
)

# ========================================
# SESSION FACTORY
# ========================================
# SessionLocal is a factory for creating database sessions
# Each session represents a "unit of work" (transaction)
SessionLocal = sessionmaker(
    # Bind to our engine
    bind=engine,
    
    # autocommit=False: We explicitly control when to commit
    # This prevents accidental commits and gives us transaction control
    autocommit=False,
    
    # autoflush=False: We explicitly control when to flush
    # Flushing sends pending changes to the database (but doesn't commit)
    autoflush=False,
)

# ========================================
# BASE CLASS FOR MODELS
# ========================================
# All ORM models inherit from this Base class
# declarative_base() provides the mapping between Python classes and database tables
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database Session Dependency for FastAPI
    
    This function creates a database session and automatically:
    1. Opens a connection
    2. Yields the session for use in the endpoint
    3. Closes the connection when done
    4. Rolls back if an exception occurred
    
    The "yield" keyword makes this a generator function.
    FastAPI's Depends() system works perfectly with generators for cleanup.
    
    Returns:
        Generator yielding a database session
        
    Usage in FastAPI:
        from fastapi import Depends
        from sqlalchemy.orm import Session
        from app.db.connection import get_db
        
        @app.get("/batches")
        def list_batches(db: Session = Depends(get_db)):
            # db is automatically injected
            batches = db.query(PayrollBatch).all()
            return batches
            # Session is automatically closed after this function returns
    
    How it works:
        1. FastAPI calls get_db()
        2. A session is created with SessionLocal()
        3. The session is yielded to the endpoint function
        4. Your endpoint code runs with the session
        5. After the endpoint returns, cleanup code after yield runs
        6. The session is closed
    """
    # Create a new database session
    db = SessionLocal()
    
    try:
        # Yield the session to the caller (FastAPI endpoint)
        # Everything after "yield" is cleanup code that runs after the endpoint
        yield db
        
    except Exception as e:
        # If an exception occurred, rollback any pending changes
        # This ensures the database stays in a consistent state
        logger.error(
            "Database session error, rolling back",
            extra={"error": str(e)},
            exc_info=True
        )
        db.rollback()
        raise
        
    finally:
        # Always close the session, even if an exception occurred
        # This returns the connection to the pool
        db.close()


def init_db() -> None:
    """
    Initialize Database Tables
    
    This function creates all tables defined in our models.
    It's called once at application startup.
    
    In production, use Alembic migrations instead!
    This function is useful for development and testing.
    
    Usage:
        from app.db.connection import init_db
        
        # At application startup
        init_db()
    """
    # Import all models so they're registered with Base
    # This ensures Base.metadata knows about all tables
    from app.db import models  # noqa: F401
    
    logger.info("Creating database tables")
    
    # Create all tables that don't exist yet
    # This does NOT modify existing tables
    # For schema changes, use Alembic migrations
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables created successfully")

