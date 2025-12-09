"""
Course Recommendations Module

This module handles course recommendation logic:
- Course filtering and reranking
- Distribution requirement lookups
- Recommendation pipeline
- Course data loading and matching
"""

from server.recommendations.course_recommender import (
    get_student_data,
    load_course_details,
    load_distribution_mapping,
    get_courses_by_distribution,
    match_course_code,
    extract_course_details,
    get_available_courses_for_prompt,
    get_vector_based_recommendations,
    build_recommendation_prompt,
    vector_search_courses,
    filter_and_rerank_courses,
    build_query_from_student_data,
    generate_and_store_course_embeddings,
    get_course_embeddings_from_db,
)

__all__ = [
    'get_student_data',
    'load_course_details',
    'load_distribution_mapping',
    'get_courses_by_distribution',
    'match_course_code',
    'extract_course_details',
    'get_available_courses_for_prompt',
    'get_vector_based_recommendations',
    'build_recommendation_prompt',
    'vector_search_courses',
    'filter_and_rerank_courses',
    'build_query_from_student_data',
    'generate_and_store_course_embeddings',
    'get_course_embeddings_from_db',
]

