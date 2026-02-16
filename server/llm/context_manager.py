"""
Context Manager for Chat Conversations

This module provides functionality to:
1. Determine if queries are related (e.g., follow-up questions)
2. Build conversation history context
3. Extract key information from previous messages to enhance current query understanding
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime


def are_queries_related(
    current_query: str,
    previous_queries: List[str],
    previous_responses: List[str],
    threshold: float = 0.3
) -> Tuple[bool, Optional[str]]:
    """
    Determine if the current query is related to previous queries in the conversation.
    Optimized for performance - returns early if no previous queries exist.
    """
    # Fast path: no previous queries means not related
    if not previous_queries:
        return False, None
    """
    Determine if the current query is related to previous queries in the conversation.
    
    Args:
        current_query: The current user query
        previous_queries: List of previous user queries in chronological order
        previous_responses: List of previous model responses in chronological order
        threshold: Minimum score to consider queries related (0.0 to 1.0)
    
    Returns:
        Tuple of (is_related: bool, context_summary: Optional[str])
        context_summary contains key information from previous messages if related
    """
    if not previous_queries:
        return False, None
    
    current_lower = current_query.lower()
    
    # Extract key entities from current query
    current_entities = _extract_entities(current_query)
    
    # Check for explicit continuation indicators
    continuation_keywords = [
        'not in', 'not from', 'excluding', 'except', 'but not',
        'also', 'and', 'plus', 'additionally', 'furthermore',
        'what about', 'how about', 'tell me more', 'more',
        'different', 'other', 'instead', 'rather',
        'but', 'however', 'although', 'though'
    ]
    
    has_continuation = any(keyword in current_lower for keyword in continuation_keywords)
    
    # Check if current query references previous context
    references_previous = _references_previous_context(
        current_query, previous_queries, previous_responses
    )
    
    # Extract entities from previous queries
    previous_entities = []
    for prev_query in previous_queries:
        prev_entities = _extract_entities(prev_query)
        previous_entities.append(prev_entities)  # Append the dictionary, don't extend
    
    # Check for entity overlap
    entity_overlap = _calculate_entity_overlap(current_entities, previous_entities)
    
    # Determine if related
    is_related = (
        has_continuation or 
        references_previous or 
        entity_overlap > threshold
    )
    
    if is_related:
        # Build context summary from previous messages
        context_summary = _build_context_summary(
            previous_queries, previous_responses, current_entities
        )
        return True, context_summary
    
    return False, None


def _extract_entities(query: str) -> Dict[str, List[str]]:
    """
    Extract key entities from a query:
    - Distribution requirements (CD, HA, LA, etc.)
    - Department codes (AAS, COS, HIS, etc.)
    - Course codes (COS 226, MAT 201, etc.)
    - Subject areas (history, computer science, etc.)
    """
    entities = {
        'distribution_codes': [],
        'department_codes': [],
        'course_codes': [],
        'subject_areas': []
    }
    
    query_upper = query.upper()
    query_lower = query.lower()
    
    # Distribution requirement codes - optimized single pattern match
    # First check for short codes (most common)
    dist_code_pattern = r'\b(CD|EC|EM|HA|LA|QCR|SEL|SEN|SA|STL|STN|QR)\b'
    dist_code_matches = re.findall(dist_code_pattern, query_upper)
    
    # Normalize distribution codes
    dist_mapping = {
        'STL': 'SEL',
        'STN': 'SEN',
        'QR': 'QCR'
    }
    
    for match in dist_code_matches:
        normalized = dist_mapping.get(match, match)
        if normalized not in entities['distribution_codes']:
            entities['distribution_codes'].append(normalized)
    
    # Then check for full phrases (less common, so check only if no codes found)
    if not entities['distribution_codes']:
        dist_phrase_pattern = r'\b(culture and difference|epistemology and cognition|ethical thought|historical analysis|literature and the arts|quantitative and computational reasoning|science and engineering|social analysis)\b'
        phrase_matches = re.findall(dist_phrase_pattern, query_lower)
        
        phrase_mapping = {
            'culture and difference': 'CD',
            'epistemology and cognition': 'EC',
            'ethical thought': 'EM',
            'historical analysis': 'HA',
            'literature and the arts': 'LA',
            'quantitative and computational reasoning': 'QCR',
            'science and engineering': 'SEN',  # Default to SEN
            'social analysis': 'SA'
        }
        
        for match in phrase_matches:
            normalized = phrase_mapping.get(match, match.upper())
            if normalized not in entities['distribution_codes']:
                entities['distribution_codes'].append(normalized)
    
    # Course codes (e.g., "COS 226", "MAT 201")
    course_pattern = r'\b([A-Z]{2,4})\s*(\d{3})\b'
    course_matches = re.findall(course_pattern, query_upper)
    for subject, number in course_matches:
        course_code = f"{subject} {number}"
        if course_code not in entities['course_codes']:
            entities['course_codes'].append(course_code)
    
    # Department codes (2-4 uppercase letters, but not course codes)
    # Use a single regex pattern to find all potential department codes, then filter
    # This is faster than checking each department individually
    dept_pattern = r'\b([A-Z]{2,4})\b'
    potential_depts = set(re.findall(dept_pattern, query_upper))
    
    # Common department codes (as a set for O(1) lookup)
    common_depts = {
        'AAS', 'AMS', 'ANT', 'ART', 'AST', 'ATL', 'BCS', 'CBE', 'CHM', 'CLA',
        'COM', 'COS', 'CWR', 'EAS', 'ECE', 'ECO', 'EEB', 'EGR', 'ENG', 'ENT',
        'ENV', 'EPS', 'FIN', 'FRE', 'GEO', 'GER', 'GHP', 'GLS', 'GSS', 'HIS',
        'HLS', 'HOS', 'HUM', 'ISC', 'ITA', 'JPN', 'JRN', 'LAS', 'LAT', 'LIN',
        'MAE', 'MAT', 'MED', 'MOL', 'MUS', 'NES', 'NEU', 'ORF', 'PAW', 'PER',
        'PHI', 'PHY', 'POL', 'POR', 'PSY', 'REL', 'RUS', 'SLA', 'SOC', 'SPA',
        'SPI', 'STC', 'THR', 'TUR', 'URB', 'VIS', 'WWS'
    }
    
    # Check which potential departments are valid and not part of course codes
    course_code_set = {code.replace(' ', '') for code in entities['course_codes']}
    for dept in potential_depts:
        if dept in common_depts:
            # Make sure it's not part of a course code
            if dept not in course_code_set and dept not in entities['department_codes']:
                entities['department_codes'].append(dept)
    
    # Subject area keywords
    subject_keywords = {
        'computer science': 'COS', 'cs': 'COS', 'programming': 'COS',
        'economics': 'ECO', 'history': 'HIS', 'philosophy': 'PHI',
        'math': 'MAT', 'mathematics': 'MAT', 'physics': 'PHY',
        'chemistry': 'CHM', 'biology': 'MOL', 'english': 'ENG',
        'literature': 'ENG', 'politics': 'POL', 'psychology': 'PSY',
        'sociology': 'SOC', 'art': 'ART', 'music': 'MUS', 'theater': 'THR'
    }
    
    for keyword, dept in subject_keywords.items():
        if keyword in query_lower:
            if dept not in entities['department_codes']:
                entities['department_codes'].append(dept)
            entities['subject_areas'].append(keyword)
    
    return entities


def _references_previous_context(
    current_query: str,
    previous_queries: List[str],
    previous_responses: List[str]
) -> bool:
    """
    Check if current query references previous context using pronouns, 
    demonstratives, or implicit references.
    """
    current_lower = current_query.lower()
    
    # Pronouns and demonstratives that suggest continuation
    continuation_words = [
        'it', 'that', 'this', 'those', 'these', 'them',
        'the same', 'the one', 'those ones',
        'the course', 'the class', 'the requirement'
    ]
    
    # Check for continuation words
    has_continuation_word = any(
        word in current_lower for word in continuation_words
    )
    
    # Check if query is very short (likely a follow-up)
    is_short_followup = len(current_query.split()) <= 5
    
    # Check if query starts with negation or exclusion
    starts_with_exclusion = any(
        current_lower.startswith(prefix) for prefix in [
            'not ', 'not in', 'not from', 'excluding', 'except',
            'but not', 'but not in', 'but not from'
        ]
    )
    
    return has_continuation_word or (is_short_followup and starts_with_exclusion)


def _calculate_entity_overlap(
    current_entities: Dict[str, List[str]],
    previous_entities: List[Dict[str, List[str]]]
) -> float:
    """
    Calculate overlap score between current and previous entities.
    Returns a score between 0.0 and 1.0.
    """
    if not previous_entities:
        return 0.0
    
    # Flatten previous entities
    prev_dist = set()
    prev_dept = set()
    prev_course = set()
    prev_subject = set()
    
    for entities in previous_entities:
        prev_dist.update(entities.get('distribution_codes', []))
        prev_dept.update(entities.get('department_codes', []))
        prev_course.update(entities.get('course_codes', []))
        prev_subject.update(entities.get('subject_areas', []))
    
    # Calculate overlaps
    current_dist = set(current_entities.get('distribution_codes', []))
    current_dept = set(current_entities.get('department_codes', []))
    current_course = set(current_entities.get('course_codes', []))
    current_subject = set(current_entities.get('subject_areas', []))
    
    # Weighted overlap calculation
    dist_overlap = len(current_dist & prev_dist) / max(len(current_dist | prev_dist), 1)
    dept_overlap = len(current_dept & prev_dept) / max(len(current_dept | prev_dept), 1)
    course_overlap = len(current_course & prev_course) / max(len(current_course | prev_course), 1)
    subject_overlap = len(current_subject & prev_subject) / max(len(current_subject | prev_subject), 1)
    
    # Weighted average (distribution and course codes are more important)
    total_overlap = (
        dist_overlap * 0.4 +
        course_overlap * 0.3 +
        dept_overlap * 0.2 +
        subject_overlap * 0.1
    )
    
    return total_overlap


def _build_context_summary(
    previous_queries: List[str],
    previous_responses: List[str],
    current_entities: Dict[str, List[str]]
) -> str:
    """
    Build a summary of relevant context from previous messages.
    """
    context_parts = []
    
    # Get the most recent query and response
    if previous_queries:
        most_recent_query = previous_queries[-1]
        context_parts.append("PREVIOUS CONVERSATION CONTEXT:")
        context_parts.append(f"Previous query: {most_recent_query}")
        
        if previous_responses and len(previous_responses) >= len(previous_queries):
            most_recent_response = previous_responses[-1]
            # Extract key info from response (first 200 chars)
            response_summary = most_recent_response[:200] + "..." if len(most_recent_response) > 200 else most_recent_response
            context_parts.append(f"Previous response summary: {response_summary}")
        
        context_parts.append("")
        context_parts.append("IMPORTANT: The current query appears to be a follow-up or continuation of the previous conversation.")
        context_parts.append("Use the context from the previous query to understand what the student is referring to.")
        context_parts.append("")
        
        # Extract entities from previous query to help understand current query
        prev_entities = _extract_entities(most_recent_query)
        
        # If current query mentions a department but previous query mentioned a requirement,
        # combine them (e.g., "CD requirement" + "not in AAS" = "CD requirement not in AAS")
        if prev_entities.get('distribution_codes') and current_entities.get('department_codes'):
            dist_codes = ', '.join(prev_entities['distribution_codes'])
            dept_codes = ', '.join(current_entities['department_codes'])
            context_parts.append(f"CONTEXT COMBINATION: The student previously asked about {dist_codes} requirement(s).")
            context_parts.append(f"The current query mentions department(s): {dept_codes}.")
            context_parts.append(f"INTERPRETATION: The student likely wants {dist_codes} requirement(s) NOT in {dept_codes} department(s).")
            context_parts.append("")
        
        # If previous query mentioned a requirement and current query is exclusionary
        if prev_entities.get('distribution_codes'):
            dist_codes = ', '.join(prev_entities['distribution_codes'])
            context_parts.append(f"Remember: The student is asking about {dist_codes} requirement(s) from the previous query.")
            context_parts.append("")
    
    return "\n".join(context_parts)


def build_conversation_history(
    user_messages: List[Dict],
    model_messages: List[Dict],
    max_messages: int = 10
) -> List[Dict[str, str]]:
    """
    Build conversation history in OpenAI message format.
    
    Args:
        user_messages: List of user message dictionaries with 'message' and 'timestamp' keys
        model_messages: List of model message dictionaries with 'message' and 'timestamp' keys
        max_messages: Maximum number of message pairs to include
    
    Returns:
        List of message dictionaries in OpenAI format: [{"role": "user", "content": "..."}, ...]
    """
    # Sort messages by timestamp
    all_messages = []
    
    for msg in user_messages:
        all_messages.append({
            'role': 'user',
            'content': msg.get('message', ''),
            'timestamp': msg.get('timestamp', datetime.now())
        })
    
    for msg in model_messages:
        all_messages.append({
            'role': 'assistant',
            'content': msg.get('message', ''),
            'timestamp': msg.get('timestamp', datetime.now())
        })
    
    # Sort by timestamp
    all_messages.sort(key=lambda x: x['timestamp'])
    
    # Take the most recent messages (up to max_messages pairs)
    recent_messages = all_messages[-(max_messages * 2):] if len(all_messages) > max_messages * 2 else all_messages
    
    # Convert to OpenAI format (remove timestamp)
    formatted_messages = []
    for msg in recent_messages:
        formatted_messages.append({
            'role': msg['role'],
            'content': msg['content']
        })
    
    return formatted_messages


def enhance_query_with_context(
    current_query: str,
    previous_queries: List[str],
    previous_responses: List[str]
) -> str:
    """
    Enhance the current query by combining it with relevant context from previous messages.
    
    Returns:
        Enhanced query string that includes context when queries are related
    """
    is_related, context_summary = are_queries_related(
        current_query, previous_queries, previous_responses
    )
    
    if is_related and context_summary:
        # Combine context with current query
        enhanced_query = f"{context_summary}\n\nCURRENT QUERY: {current_query}"
        return enhanced_query
    
    return current_query

