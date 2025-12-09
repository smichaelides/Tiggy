"""
Vector Search and Embeddings Module

This module handles all vector search and embedding functionality:
- Embedding generation and storage
- Vector similarity search
- Course embedding utilities
"""

from server.search.embeddings import (
    embedding_from_string,
    cosine_similarity,
    find_similar_courses,
    recommendations_from_strings
)

__all__ = [
    'embedding_from_string',
    'cosine_similarity',
    'find_similar_courses',
    'recommendations_from_strings',
]

