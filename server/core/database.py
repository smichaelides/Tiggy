import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Try to import Flask's g, but don't fail if not available (for standalone scripts)
try:
    from flask import g
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    g = None


load_dotenv()

CONNECTION_STRING = os.environ["MONGODB_CONNECTION_STRING"]
DATABASE_NAME = os.environ["DATABASE_NAME"]


def get_database():
    """
    Get database connection for use within Flask application context.
    Uses Flask's g object for connection caching.
    """
    if not FLASK_AVAILABLE or g is None:
        raise RuntimeError(
            "get_database() requires Flask application context. "
            "For standalone scripts, use get_database_standalone() instead."
        )
    
    if 'db' not in g:
        client: MongoClient[dict[str, object]] = MongoClient(CONNECTION_STRING)

        try:
            client.admin.command("ping")
            logging.info("Connected to MongoDB; using database %s", DATABASE_NAME)
            g.db = client[DATABASE_NAME]
        except Exception as ex:
            logging.error(
                "An error occurred while creating the database client: %s", ex
            )
            raise

    return g.db


def get_database_standalone():
    """
    Get database connection for use in standalone scripts (outside Flask).
    Creates a new connection each time (no caching).
    """
    client: MongoClient[dict[str, object]] = MongoClient(CONNECTION_STRING)
    
    try:
        client.admin.command("ping")
        logging.info("Connected to MongoDB; using database %s", DATABASE_NAME)
        db = client[DATABASE_NAME]
        return db
    except Exception as ex:
        logging.error(
            "An error occurred while creating the database client: %s", ex
        )
        raise
