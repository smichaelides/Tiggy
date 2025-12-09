"""
Script to generate and store embeddings for all courses.
Run this once to populate the database with course embeddings.

Usage:
    # From the TigerTalks directory (project root):
    python -m server.generate_embeddings
    
    # Or from the server directory:
    python generate_embeddings.py
"""
import sys
import os
from pathlib import Path
import logging

# Add the parent directory to Python path so we can import server modules
# This allows the script to be run from either the server/ or project root directory
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from server.recommendations.course_recommender import generate_and_store_course_embeddings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    logging.info("Starting embedding generation for all courses...")
    try:
        generate_and_store_course_embeddings(
            model="text-embedding-3-small",  # Can use "text-embedding-3-large" for better quality
            batch_size=50,  # Process 50 courses at a time
            use_standalone=True  # Use standalone database connection (outside Flask)
        )
        logging.info("Successfully completed embedding generation!")
    except Exception as e:
        logging.error(f"Failed to generate embeddings: {e}", exc_info=True)
        raise
