"""
Utility functions for generating and working with embeddings for course recommendations.
"""
import logging
import numpy as np
from typing import List, Tuple
from server.services.openai_service import get_openai_client


def embedding_from_string(string: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    Generate an embedding for a given string using OpenAI's embedding API.
    
    Args:
        string: The text to embed
        model: The embedding model to use (default: "text-embedding-3-small")
    
    Returns:
        List of floats representing the embedding vector
    """
    client = get_openai_client()
    
    try:
        response = client.embeddings.create(
            model=model,
            input=string
        )
        return response.data[0].embedding
    except Exception as e:
        logging.error(f"Failed to generate embedding: {e}")
        raise


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First embedding vector
        vec2: Second embedding vector
    
    Returns:
        Cosine similarity score between -1 and 1 (higher = more similar)
    """
    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)
    
    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def distances_from_embeddings(
    query_embedding: List[float],
    embeddings: List[List[float]],
    distance_metric: str = "cosine"
) -> List[float]:
    """
    Calculate distances between a query embedding and a list of embeddings.
    
    Args:
        query_embedding: The query embedding vector
        embeddings: List of embedding vectors to compare against
        distance_metric: "cosine" for cosine similarity (1 - similarity), or "euclidean"
    
    Returns:
        List of distances (lower = more similar for cosine, higher = more similar for euclidean)
    """
    if distance_metric == "cosine":
        # For cosine, we return 1 - similarity (so lower = more similar)
        return [1.0 - cosine_similarity(query_embedding, emb) for emb in embeddings]
    elif distance_metric == "euclidean":
        query_array = np.array(query_embedding)
        distances = []
        for emb in embeddings:
            emb_array = np.array(emb)
            distance = np.linalg.norm(query_array - emb_array)
            distances.append(distance)
        return distances
    else:
        raise ValueError(f"Unknown distance metric: {distance_metric}")


def indices_of_nearest_neighbors_from_distances(distances: List[float]) -> List[int]:
    """
    Get indices of nearest neighbors sorted by distance (ascending).
    
    Args:
        distances: List of distances
    
    Returns:
        List of indices sorted by distance (closest first)
    """
    # Create list of (index, distance) tuples
    indexed_distances = [(i, dist) for i, dist in enumerate(distances)]
    # Sort by distance (ascending)
    sorted_distances = sorted(indexed_distances, key=lambda x: x[1])
    # Return just the indices
    return [idx for idx, _ in sorted_distances]


def recommendations_from_strings(
    strings: List[str],
    index_of_source_string: int,
    model: str = "text-embedding-3-small",
) -> List[int]:
    """
    Return nearest neighbors of a given string based on embeddings.
    
    Args:
        strings: List of strings to compare
        index_of_source_string: Index of the source string to find neighbors for
        model: Embedding model to use
    
    Returns:
        List of indices sorted by similarity (most similar first, excluding the source itself)
    """
    if index_of_source_string >= len(strings):
        raise ValueError(f"Source index {index_of_source_string} out of range")
    
    # Get embeddings for all strings
    logging.info(f"Generating embeddings for {len(strings)} strings...")
    embeddings = []
    for i, string in enumerate(strings):
        if i % 100 == 0:
            logging.info(f"Processing embedding {i}/{len(strings)}")
        embeddings.append(embedding_from_string(string, model=model))
    
    # Get the embedding of the source string
    query_embedding = embeddings[index_of_source_string]
    
    # Get distances between the source embedding and other embeddings
    distances = distances_from_embeddings(query_embedding, embeddings, distance_metric="cosine")
    
    # Get indices of nearest neighbors
    indices_of_nearest_neighbors = indices_of_nearest_neighbors_from_distances(distances)
    
    # Remove the source string itself from results
    indices_of_nearest_neighbors = [idx for idx in indices_of_nearest_neighbors if idx != index_of_source_string]
    
    return indices_of_nearest_neighbors


def find_similar_courses(
    query_text: str,
    course_texts: List[str],
    course_codes: List[str],
    top_k: int = 20,
    model: str = "text-embedding-3-small"
) -> List[Tuple[str, float]]:
    """
    Find the top-k most similar courses to a query text.
    
    Args:
        query_text: The query text (e.g., user's request or course description)
        course_texts: List of course text representations (title + description + etc.)
        course_codes: List of course codes corresponding to course_texts
        top_k: Number of top results to return
        model: Embedding model to use
    
    Returns:
        List of tuples (course_code, similarity_score) sorted by similarity (highest first)
    """
    if len(course_texts) != len(course_codes):
        raise ValueError("course_texts and course_codes must have the same length")
    
    if len(course_texts) == 0:
        return []
    
    # Generate embedding for query
    logging.info(f"Generating embedding for query: {query_text[:100]}...")
    query_embedding = embedding_from_string(query_text, model=model)
    
    # Generate embeddings for all courses (or load from cache/DB)
    logging.info(f"Generating embeddings for {len(course_texts)} courses...")
    course_embeddings = []
    for i, course_text in enumerate(course_texts):
        if i % 100 == 0:
            logging.info(f"Processing course embedding {i}/{len(course_texts)}")
        course_embeddings.append(embedding_from_string(course_text, model=model))
    
    # Calculate similarities
    similarities = [cosine_similarity(query_embedding, emb) for emb in course_embeddings]
    
    # Create list of (course_code, similarity) tuples
    course_similarities = list(zip(course_codes, similarities))
    
    # Sort by similarity (descending)
    course_similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top-k
    return course_similarities[:top_k]
