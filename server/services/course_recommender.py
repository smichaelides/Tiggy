import os
import json
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from server.database import get_database, get_database_standalone
from server.services.embeddings_utils import (
    embedding_from_string,
    cosine_similarity,
    find_similar_courses
)

# Cache for course details JSON
_course_details_cache: Optional[Dict[str, Any]] = None
_major_requirements_cache: Optional[Dict[str, Any]] = None
_distribution_mapping_cache: Optional[Dict[str, List[str]]] = None


def _get_course_details_path() -> str:
    """Get the absolute path to spring26_course_details.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '..', 'data', 'course_info', 'spring26_course_details.json')


def _get_major_requirements_path() -> str:
    """Get the absolute path to all_major_requirements.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '..', 'data', 'course_info', 'all_major_requirements.json')


def _get_distribution_mapping_path() -> str:
    """Get the absolute path to distribution_to_courses.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '..', 'data', 'course_info', 'distribution_to_courses.json')


def load_distribution_mapping() -> Dict[str, List[str]]:
    """
    Load and parse distribution_to_courses.json with caching.
    Returns a dictionary mapping distribution codes to lists of course codes.
    Example: {"CD": ["AAS 232", ...], "SEL": ["ARC 311", ...]}
    """
    global _distribution_mapping_cache
    
    if _distribution_mapping_cache is not None:
        return _distribution_mapping_cache
    
    file_path = _get_distribution_mapping_path()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _distribution_mapping_cache = json.load(f)
        logging.info("Loaded distribution mapping from %s", file_path)
        return _distribution_mapping_cache
    except FileNotFoundError:
        logging.error("Distribution mapping file not found: %s", file_path)
        return {}
    except json.JSONDecodeError as e:
        logging.error("Failed to parse distribution mapping JSON: %s", e)
        return {}
    except Exception as e:
        logging.error("Unexpected error loading distribution mapping: %s", e)
        return {}


def get_courses_by_distribution(
    distribution_code: str,
    past_courses: Optional[Dict[str, str]] = None,
    exclude_taken: bool = True
) -> List[str]:
    """
    Get list of course codes that fulfill a distribution requirement.
    This is a simple lookup from the pre-generated distribution_to_courses.json.
    
    Args:
        distribution_code: Distribution requirement code (e.g., "SEL", "SEN", "HA", "LA", "CD")
        past_courses: Optional dict of past course codes to grades (to exclude)
        exclude_taken: If True, exclude courses already taken
    
    Returns:
        List of course codes that fulfill the distribution requirement
    """
    distribution_mapping = load_distribution_mapping()
    
    # Normalize distribution code
    distribution_code_upper = distribution_code.upper()
    distribution_code_mapping = {
        'STL': 'SEL',
        'STN': 'SEN',
        'QR': 'QCR'
    }
    normalized_code = distribution_code_mapping.get(distribution_code_upper, distribution_code_upper)
    
    # Get courses for this distribution
    matching_courses = distribution_mapping.get(normalized_code, [])
    
    # Exclude already taken courses if requested
    if exclude_taken and past_courses:
        matching_courses = [code for code in matching_courses if code not in past_courses]
    
    logging.info(f"Found {len(matching_courses)} courses with distribution code {normalized_code}")
    return matching_courses


def load_course_details() -> Dict[str, Any]:
    """
    Load and parse spring26_course_details.json with caching.
    Returns the parsed JSON data.
    """
    global _course_details_cache
    
    if _course_details_cache is not None:
        return _course_details_cache
    
    file_path = _get_course_details_path()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _course_details_cache = json.load(f)
        logging.info("Loaded course details from %s", file_path)
        return _course_details_cache
    except FileNotFoundError:
        logging.error("Course details file not found: %s", file_path)
        raise
    except json.JSONDecodeError as e:
        logging.error("Failed to parse course details JSON: %s", e)
        raise
    except Exception as e:
        logging.error("Unexpected error loading course details: %s", e)
        raise


def match_course_code(course_code: str) -> Optional[Dict[str, Any]]:
    """
    Match a course code (e.g., "COS 126" or "COS126") to a course object in the JSON.
    
    Args:
        course_code: Course code in format "SUBJECT NUMBER" or "SUBJECTNUMBER"
    
    Returns:
        Course object from JSON if found, None otherwise
    """
    course_details = load_course_details()
    
    # Normalize course code: remove spaces and convert to uppercase
    normalized_code = course_code.replace(' ', '').upper()
    
    # Parse subject and catalog number
    # Try to find where the number starts (first digit)
    subject = None
    catalog_number = None
    
    for i, char in enumerate(normalized_code):
        if char.isdigit():
            subject = normalized_code[:i]
            catalog_number = normalized_code[i:]
            break
    
    if not subject or not catalog_number:
        logging.warning("Invalid course code format: %s", course_code)
        return None
    
    # Search through the course details
    if 'term' not in course_details or not course_details['term']:
        logging.warning("No term data found in course details")
        return None
    
    # Get the first term (Spring 2026)
    term = course_details['term'][0]
    
    if 'subjects' not in term:
        logging.warning("No subjects found in term")
        return None
    
    # Search through all subjects
    for subject_obj in term.get('subjects', []):
        if subject_obj.get('code', '').upper() == subject:
            # Found matching subject, search courses
            for course in subject_obj.get('courses', []):
                if course.get('catalog_number') == catalog_number:
                    return course
            
            # Also check crosslistings
            for course in subject_obj.get('courses', []):
                for crosslisting in course.get('crosslistings', []):
                    if (crosslisting.get('subject', '').upper() == subject and 
                        crosslisting.get('catalog_number') == catalog_number):
                        return course
    
    logging.debug("Course not found: %s", course_code)
    return None


def get_student_data(user_id: str) -> Dict[str, Any]:
    """
    Fetch student data from the database.
    
    Args:
        user_id: MongoDB ObjectId string of the user
    
    Returns:
        Dictionary with keys:
        - past_courses: Dict[str, str] mapping course codes to grades
        - concentration: Optional[str] major/concentration
        - grade: Optional[str] class year
    """
    db = get_database()
    
    try:
        db_user = db.users.find_one({"_id": ObjectId(user_id)})
        if not db_user:
            logging.warning("User not found: %s", user_id)
            return {
                "past_courses": {},
                "concentration": None,
                "grade": None
            }
        
        # Extract relevant fields
        past_courses = db_user.get("past_courses", {})
        concentration = db_user.get("concentration")
        grade = db_user.get("grade")
        
        # Ensure past_courses is a dict
        if not isinstance(past_courses, dict):
            past_courses = {}
        
        return {
            "past_courses": past_courses,
            "concentration": concentration,
            "grade": grade
        }
    except Exception as e:
        logging.error("Failed to fetch student data for user %s: %s", user_id, e)
        return {
            "past_courses": {},
            "concentration": None,
            "grade": None
        }


def load_major_requirements() -> Dict[str, Any]:
    """
    Load and parse all_major_requirements.json with caching.
    Returns the parsed JSON data.
    """
    global _major_requirements_cache
    
    if _major_requirements_cache is not None:
        return _major_requirements_cache
    
    file_path = _get_major_requirements_path()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _major_requirements_cache = json.load(f)
        logging.info("Loaded major requirements from %s", file_path)
        return _major_requirements_cache
    except FileNotFoundError:
        logging.error("Major requirements file not found: %s", file_path)
        raise
    except json.JSONDecodeError as e:
        logging.error("Failed to parse major requirements JSON: %s", e)
        raise
    except Exception as e:
        logging.error("Unexpected error loading major requirements: %s", e)
        raise


def get_major_courses(department_code: str) -> List[str]:
    """
    Get list of course codes for a department from course details.
    
    Args:
        department_code: Department code (e.g., "COS")
    
    Returns:
        List of course codes (e.g., ["COS 126", "COS 217", ...])
    """
    if not department_code:
        return []
    
    return _get_department_courses(department_code)


def _get_department_courses(department_code: str) -> List[str]:
    """
    Get all course codes for a department from course details.
    
    Args:
        department_code: Department code (e.g., "COS")
    
    Returns:
        List of course codes in format "DEPT NUMBER"
    """
    course_details = load_course_details()
    course_codes = []
    
    if 'term' not in course_details or not course_details['term']:
        return course_codes
    
    term = course_details['term'][0]
    
    for subject_obj in term.get('subjects', []):
        if subject_obj.get('code', '').upper() == department_code.upper():
            for course in subject_obj.get('courses', []):
                catalog_num = course.get('catalog_number')
                if catalog_num:
                    course_codes.append(f"{department_code} {catalog_num}")
            break
    
    return course_codes


def get_available_courses_for_prompt(
    past_courses: Dict[str, str],
    concentration: Optional[str] = None
) -> List[str]:
    """
    Get list of available course codes for the prompt.
    If past courses exist, return broader set. If no past courses, filter by major.
    
    Args:
        past_courses: Dict of past course codes to grades
        concentration: Major/concentration name
    
    Returns:
        List of course codes available for recommendation
    """
    course_details = load_course_details()
    available_courses = []
    
    if not past_courses and concentration:
        # No past courses - filter by department code
        # concentration is expected to be a department code like "COS"
        major_courses = get_major_courses(concentration)
        available_courses = major_courses
    else:
        # Past courses exist - get broader set of all courses
        if 'term' not in course_details or not course_details['term']:
            return available_courses
        
        term = course_details['term'][0]
        for subject_obj in term.get('subjects', []):
            subject_code = subject_obj.get('code', '')
            for course in subject_obj.get('courses', []):
                catalog_num = course.get('catalog_number')
                if catalog_num:
                    course_code = f"{subject_code} {catalog_num}"
                    # Exclude courses already taken
                    if course_code not in past_courses:
                        available_courses.append(course_code)
    
    return available_courses


def filter_courses_by_distribution(
    distribution_code: str,
    past_courses: Optional[Dict[str, str]] = None,
    exclude_taken: bool = True
) -> List[str]:
    """
    Filter courses by distribution requirement code (e.g., "SEL", "SEN", "HA").
    This is a simple filter that directly checks the distribution field in the JSON.
    
    Args:
        distribution_code: Distribution requirement code (e.g., "SEL", "SEN", "HA", "LA")
        past_courses: Optional dict of past course codes to grades (to exclude)
        exclude_taken: If True, exclude courses already taken
    
    Returns:
        List of course codes that fulfill the distribution requirement
    """
    course_details = load_course_details()
    matching_courses = []
    
    if 'term' not in course_details or not course_details['term']:
        return matching_courses
    
    term = course_details['term'][0]
    distribution_code_upper = distribution_code.upper()
    
    # Normalize distribution code (handle variations)
    distribution_mapping = {
        'STL': 'SEL',  # Some systems use STL instead of SEL
        'STN': 'SEN',  # Some systems use STN instead of SEN
        'QR': 'QCR'    # Some systems use QR instead of QCR
    }
    normalized_code = distribution_mapping.get(distribution_code_upper, distribution_code_upper)
    
    for subject_obj in term.get('subjects', []):
        subject_code = subject_obj.get('code', '')
        for course in subject_obj.get('courses', []):
            catalog_num = course.get('catalog_number')
            if not catalog_num:
                continue
            
            course_code = f"{subject_code} {catalog_num}"
            
            # Skip if already taken
            if exclude_taken and past_courses and course_code in past_courses:
                continue
            
            # Check distribution field
            detail = course.get('detail', {})
            distribution = detail.get('distribution', '')
            
            # Handle both list and string formats
            if isinstance(distribution, list):
                dist_codes = [str(d).strip().upper() for d in distribution if d]
                if normalized_code in dist_codes or distribution_code_upper in dist_codes:
                    matching_courses.append(course_code)
            elif isinstance(distribution, str):
                # Check if the code appears in the string
                dist_upper = distribution.upper()
                if normalized_code in dist_upper or distribution_code_upper in dist_upper:
                    # More careful check - split by common delimiters
                    dist_parts = [d.strip().upper() for d in dist_upper.replace(',', ' ').split()]
                    if normalized_code in dist_parts or distribution_code_upper in dist_parts:
                        matching_courses.append(course_code)
    
    logging.info(f"Found {len(matching_courses)} courses with distribution code {distribution_code}")
    return matching_courses


def get_vector_based_recommendations(
    student_data: Dict[str, Any],
    user_query: Optional[str] = None,
    top_k: int = 50,
    final_count: int = 15
) -> List[str]:
    """
    Get course recommendations using vector search pipeline:
    1. Vector search for semantic matches
    2. Filter by constraints (past courses, level, etc.)
    3. Rerank by personalization
    4. Return top candidates for LLM
    
    Args:
        student_data: Dictionary with past_courses, concentration, grade
        user_query: Optional user query text
        top_k: Number of top vector results to retrieve
        final_count: Number of candidates to return for LLM
    
    Returns:
        List of course codes (top candidates)
    """
    # Build query text
    query_text = build_query_from_student_data(student_data, user_query)
    
    # Get available courses (excluding past courses)
    past_courses = student_data.get("past_courses", {})
    
    # Check if this is a similarity query - if so, don't filter by major
    is_similarity_query = False
    if user_query:
        query_lower = user_query.lower()
        similarity_keywords = ['similar to', 'like', 'same as', 'equivalent to', 'comparable to', 'related to']
        is_similarity_query = any(keyword in query_lower for keyword in similarity_keywords)
    
    # For similarity queries, search ALL courses (not just major-related)
    # For other queries, filter by available courses
    if is_similarity_query:
        available_courses = None  # Search all courses for similarity
        logging.info("Similarity query detected - searching all courses, not filtering by major")
    else:
        available_courses = get_available_courses_for_prompt(
            past_courses=past_courses,
            concentration=student_data.get("concentration")
        )
    
    # Perform vector search
    logging.info(f"Performing vector search with query: {query_text[:100]}...")
    vector_results = vector_search_courses(
        query_text=query_text,
        available_course_codes=available_courses,
        top_k=top_k
    )
    
    if not vector_results:
        logging.warning("No vector search results found, falling back to available courses")
        return available_courses[:final_count] if available_courses else []
    
    # Filter and rerank
    grade = student_data.get("grade")
    concentration = student_data.get("concentration")
    
    # Determine max level based on grade
    max_level = None
    if grade:
        if grade.lower() in ["freshman", "first-year"]:
            max_level = 200
        elif grade.lower() in ["sophomore"]:
            max_level = 300
    
    # For similarity queries, don't boost by major (similarity is the priority)
    # For other queries, use normal filtering with major boost
    filtered_results = filter_and_rerank_courses(
        vector_results=vector_results,
        past_courses=past_courses,
        concentration=concentration if not is_similarity_query else None,  # Don't boost by major for similarity queries
        grade=grade,
        max_level=max_level,
        min_similarity=0.1  # Minimum similarity threshold
    )
    
    # Return top candidates
    candidate_codes = [code for code, _ in filtered_results[:final_count]]
    
    logging.info(f"Vector search returned {len(candidate_codes)} candidates")
    return candidate_codes


def build_recommendation_prompt(
    student_data: Dict[str, Any],
    available_courses: List[str],
    use_vector_search: bool = True,
    user_query: Optional[str] = None
) -> tuple[str, str]:
    """
    Build system prompt and context message for course recommendations.
    
    Args:
        student_data: Dictionary with past_courses, concentration, grade
        available_courses: List of available course codes
    
    Returns:
        Tuple of (system_prompt, context_message)
    """
    past_courses = student_data.get("past_courses", {})
    concentration = student_data.get("concentration")
    grade = student_data.get("grade")
    
    # If using vector search, get top candidates first
    if use_vector_search:
        candidate_courses = get_vector_based_recommendations(
            student_data=student_data,
            user_query=user_query,
            top_k=50,
            final_count=20  # Give LLM more candidates to choose from
        )
        
        # If we have candidates from vector search, use those
        if candidate_courses:
            available_courses = candidate_courses
            logging.info(f"Using {len(available_courses)} vector-selected candidates for LLM")
    
    # Build system prompt
    system_prompt = """You are a knowledgeable course advisor for Princeton University. Your role is to recommend exactly 5 courses to students based on their academic history, major, and class year.

IMPORTANT OUTPUT REQUIREMENTS:
- You must output exactly 5 course codes
- Course codes must be in the format "SUBJECT NUMBER" (e.g., "COS 126", "ECO 100")
- Output only the course codes, one per line, or as a JSON array
- Do not include explanations, descriptions, or additional text
- Only recommend courses from the available courses list provided
- Consider the student's class year to recommend appropriate course levels
- Prioritize courses that build on their past coursework if they have taken courses
- If they have no past courses, recommend foundational courses relevant to their major
- Use their past classes and grade received in class (if given) to recommend courses of appropriate difficulty
- The courses provided have been pre-selected for semantic relevance, so prioritize them"""

    # Build context message
    context_parts = []
    
    # Student profile
    context_parts.append("STUDENT PROFILE:")
    if grade:
        context_parts.append(f"- Class Year: {grade}")
    if concentration:
        context_parts.append(f"- Major/Concentration: {concentration}")
    else:
        context_parts.append("- Major/Concentration: Not specified")
    context_parts.append("")
    
    # Past courses with grades
    if past_courses:
        context_parts.append("PAST COURSES TAKEN (with grades):")
        for course_code, grade_received in past_courses.items():
            context_parts.append(f"- {course_code}: {grade_received}")
        context_parts.append("")
        context_parts.append("Based on these past courses, recommend 5 courses that would be good next steps, considering:")
        context_parts.append("- Courses that build on their existing knowledge")
        context_parts.append("- Appropriate course level for their class year")
        context_parts.append("- Logical progression in their academic journey")
    else:
        context_parts.append("PAST COURSES: None")
        context_parts.append("")
        if concentration:
            context_parts.append(f"Since the student has no past courses, recommend 5 foundational courses relevant to their {concentration} major.")
            context_parts.append("Consider appropriate course levels for their class year.")
        else:
            context_parts.append("Since the student has no past courses and no major specified, recommend 5 general foundational courses.")
            context_parts.append("Consider appropriate course levels for their class year.")
    context_parts.append("")
    
    # Available courses (limit to reasonable number for prompt)
    context_parts.append("AVAILABLE COURSES (Spring 2026):")
    if len(available_courses) > 200:
        # If too many, sample a diverse set
        sampled_courses = random.sample(available_courses, 200)
        context_parts.append(f"(Showing sample of {len(sampled_courses)} courses from {len(available_courses)} total)")
        for course_code in sorted(sampled_courses)[:200]:
            context_parts.append(f"- {course_code}")
    else:
        for course_code in sorted(available_courses):
            context_parts.append(f"- {course_code}")
    context_parts.append("")
    
    # Instruction
    context_parts.append("INSTRUCTION:")
    context_parts.append("Based on the information above, recommend exactly 5 course codes from the available courses list.")
    context_parts.append("Output only the 5 course codes, one per line, in the format 'SUBJECT NUMBER'.")
    
    context_message = "\n".join(context_parts)
    
    return system_prompt, context_message


def extract_course_details(course_code: str) -> Optional[Dict[str, Any]]:
    """
    Extract formatted course details from course code.
    Converts course code to full course object with formatted fields.
    
    Args:
        course_code: Course code in format "SUBJECT NUMBER" (e.g., "COS 126")
    
    Returns:
        Dictionary with keys:
        - code: Course code (e.g., "COS 126")
        - title: Course title
        - instructor: First instructor's full name (or "TBA" if none)
        - format: Class format (e.g., "Lecture", "Seminar") from first class
        - schedule: Formatted schedule string (e.g., "Mon, Wed 10:00-10:50 AM")
        - description: Course description
        Returns None if course not found
    """
    course_obj = match_course_code(course_code)
    
    if not course_obj:
        logging.warning(f"Course not found: {course_code}")
        return None
    
    # Extract title
    title = course_obj.get('title', '')
    
    # Extract instructor (first one)
    instructors = course_obj.get('instructors', [])
    instructor = "TBA"
    if instructors and len(instructors) > 0:
        instructor = instructors[0].get('full_name', 'TBA')
    
    # Extract format from first class
    format_type = "Unknown"
    classes = course_obj.get('classes', [])
    if classes and len(classes) > 0:
        format_type = classes[0].get('type_name', 'Unknown')
    
    # Extract and format schedule
    schedule = "TBA"
    if classes and len(classes) > 0:
        class_schedule = classes[0].get('schedule', {})
        meetings = class_schedule.get('meetings', [])
        if meetings:
            # Format the schedule
            schedule_parts = []
            for meeting in meetings:
                days = meeting.get('days', [])
                start_time = meeting.get('start_time', '')
                end_time = meeting.get('end_time', '')
                
                if days and start_time and end_time:
                    # Map day abbreviations to full names
                    day_map = {
                        'M': 'Mon',
                        'T': 'Tue',
                        'W': 'Wed',
                        'R': 'Thu',
                        'F': 'Fri',
                        'S': 'Sat',
                        'U': 'Sun'
                    }
                    days_str = ', '.join([day_map.get(day, day) for day in days])
                    schedule_parts.append(f"{days_str} {start_time}-{end_time}")
            
            if schedule_parts:
                schedule = ' | '.join(schedule_parts)
    
    # Extract description
    description = ""
    detail = course_obj.get('detail', {})
    if detail:
        description = detail.get('description', '')
    
    return {
        "code": course_code,
        "title": title,
        "instructor": instructor,
        "format": format_type,
        "schedule": schedule,
        "description": description
    }


def build_course_text_corpus(course_obj: Dict[str, Any], subject_code: str) -> str:
    """
    Build a comprehensive text representation of a course for embedding.
    Combines title, description, prerequisites, and other relevant information.
    
    Args:
        course_obj: Course object from JSON
        subject_code: Subject code (e.g., "COS")
    
    Returns:
        Combined text string representing the course
    """
    parts = []
    
    # Course code and title
    catalog_number = course_obj.get('catalog_number', '')
    title = course_obj.get('title', '')
    if title:
        parts.append(f"{subject_code} {catalog_number}: {title}")
    
    # Description
    detail = course_obj.get('detail', {})
    description = detail.get('description', '')
    if description:
        parts.append(f"Description: {description}")
    
    # Prerequisites (if available in detail or elsewhere)
    prerequisites = detail.get('prerequisites', '')
    if not prerequisites:
        # Try to get from course_obj directly
        prerequisites = course_obj.get('prerequisites', '')
    if prerequisites:
        parts.append(f"Prerequisites: {prerequisites}")
    
    # Distribution requirements (important for requirement queries)
    distribution = detail.get('distribution', '')
    if not distribution:
        distribution = course_obj.get('distribution', '')
    if distribution:
        # Handle both list format (new) and string format (legacy)
        if isinstance(distribution, list):
            dist_codes = [str(d).strip() for d in distribution if d]
            distribution_str = ', '.join(dist_codes)
        elif isinstance(distribution, str):
            # Legacy format: string that may contain comma-separated values
            dist_codes = [d.strip() for d in distribution.split(',') if d.strip()]
            distribution_str = distribution
        else:
            dist_codes = []
            distribution_str = str(distribution)
        
        # Make distribution more prominent in the text corpus
        if distribution_str:
            parts.append(f"Distribution requirement: {distribution_str}")
        
        # Add expanded description for better semantic matching
        distribution_expansions = {
            'CD': 'Culture and Difference, diversity, identity, cultural perspectives',
            'EC': 'Epistemology and Cognition, knowledge, thinking, philosophy of mind',
            'EM': 'Ethical Thought and Moral Values, ethics, morality, values',
            'HA': 'Historical Analysis, history, historical methods, past events',
            'LA': 'Literature and the Arts, creative arts, literary analysis, artistic expression',
            'QCR': 'Quantitative and Computational Reasoning, mathematics, statistics, data analysis',
            'SEL': 'Science and Engineering with Laboratory, lab work, experiments, scientific methods',
            'SEN': 'Science and Engineering No Lab, theoretical science, mathematical science',
            'SA': 'Social Analysis, social sciences, society, social structures, social behavior',
            'QR': 'Quantitative and Computational Reasoning, mathematics, statistics, data analysis',
            'STN': 'Science and Engineering No Lab, theoretical science, mathematical science',
            'STL': 'Science and Engineering with Laboratory, lab work, experiments, scientific methods'
        }
        # Process distribution codes
        for code in dist_codes:
            code_upper = code.upper()
            if code_upper in distribution_expansions:
                parts.append(f"Fulfills {code_upper}: {distribution_expansions[code_upper]}")
    
    # Track (undergraduate/graduate)
    track = detail.get('track', '')
    if track:
        parts.append(f"Level: {track}")
    
    # Instructors
    instructors = course_obj.get('instructors', [])
    if instructors:
        instructor_names = [inst.get('full_name', '') for inst in instructors if inst.get('full_name')]
        if instructor_names:
            parts.append(f"Instructors: {', '.join(instructor_names)}")
    
    # Crosslistings (can indicate related courses)
    crosslistings = course_obj.get('crosslistings', [])
    if crosslistings:
        crosslisting_codes = [
            f"{cl.get('subject', '')} {cl.get('catalog_number', '')}"
            for cl in crosslistings
        ]
        if crosslisting_codes:
            parts.append(f"Crosslisted with: {', '.join(crosslisting_codes)}")
    
    # Class format
    classes = course_obj.get('classes', [])
    if classes:
        format_types = set()
        for class_obj in classes:
            format_type = class_obj.get('type_name', '')
            if format_type:
                format_types.add(format_type)
        if format_types:
            parts.append(f"Format: {', '.join(sorted(format_types))}")
    
    return " | ".join(parts)


def get_all_courses_with_text() -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Get all courses with their text corpus and course objects.
    
    Returns:
        List of tuples: (course_code, course_text_corpus, course_obj)
    """
    course_details = load_course_details()
    courses = []
    
    if 'term' not in course_details or not course_details['term']:
        return courses
    
    term = course_details['term'][0]
    
    for subject_obj in term.get('subjects', []):
        subject_code = subject_obj.get('code', '')
        for course_obj in subject_obj.get('courses', []):
            catalog_num = course_obj.get('catalog_number', '')
            if catalog_num:
                course_code = f"{subject_code} {catalog_num}"
                course_text = build_course_text_corpus(course_obj, subject_code)
                courses.append((course_code, course_text, course_obj))
    
    return courses


def generate_and_store_course_embeddings(
    model: str = "text-embedding-3-small",
    batch_size: int = 100,
    use_standalone: bool = False
) -> None:
    """
    Generate embeddings for all courses and store them in MongoDB.
    This should be run once to populate the database with embeddings.
    
    Args:
        model: Embedding model to use
        batch_size: Number of courses to process before logging progress
        use_standalone: If True, use standalone database connection (for scripts outside Flask)
    """
    # Use standalone connection if requested (for scripts) or if Flask context not available
    try:
        if use_standalone:
            db = get_database_standalone()
        else:
            db = get_database()
    except RuntimeError:
        # Fall back to standalone if Flask context not available
        db = get_database_standalone()
    courses = get_all_courses_with_text()
    course_details = load_course_details()
    
    # Get semester code from course details
    semester_code = None
    if 'term' in course_details and course_details['term']:
        semester_code = int(course_details['term'][0].get('code', 0))
    
    logging.info(f"Generating embeddings for {len(courses)} courses...")
    
    for i, (course_code, course_text, course_obj) in enumerate(courses):
        if i % batch_size == 0:
            logging.info(f"Processing course {i}/{len(courses)}: {course_code}")
        
        try:
            # Generate embedding
            embedding = embedding_from_string(course_text, model=model)
            
            # Store in MongoDB
            # Try to find existing course document
            subject_code = course_code.split()[0]
            catalog_number = course_code.split()[1]
            
            # Update course document with embedding
            filter_query = {
                "department": subject_code,
                "catalog_number": catalog_number
            }
            if semester_code:
                filter_query["semester"] = semester_code
            
            result = db.courses.update_one(
                filter_query,
                {
                    "$set": {
                        "embedding": embedding,
                        "embedding_model": model,
                        "course_text_corpus": course_text
                    }
                },
                upsert=False  # Don't create if doesn't exist
            )
            
            # If course not in DB, store in a separate embeddings collection
            if result.matched_count == 0:
                db.course_embeddings.update_one(
                    {
                        "course_code": course_code,
                        "subject_code": subject_code,
                        "catalog_number": catalog_number
                    },
                    {
                        "$set": {
                            "course_code": course_code,
                            "subject_code": subject_code,
                            "catalog_number": catalog_number,
                            "embedding": embedding,
                            "embedding_model": model,
                            "course_text_corpus": course_text,
                            "course_obj": course_obj
                        }
                    },
                    upsert=True
                )
        
        except Exception as e:
            logging.error(f"Failed to generate embedding for {course_code}: {e}")
            continue
    
    logging.info(f"Completed generating embeddings for {len(courses)} courses")


def get_course_embeddings_from_db(use_standalone: bool = False) -> Tuple[List[str], List[str], List[List[float]]]:
    """
    Load all course embeddings from MongoDB.
    
    Args:
        use_standalone: If True, use standalone database connection (for scripts outside Flask)
    
    Returns:
        Tuple of (course_codes, course_texts, embeddings)
    """
    # Use standalone connection if requested or if Flask context not available
    try:
        if use_standalone:
            db = get_database_standalone()
        else:
            db = get_database()
    except RuntimeError:
        # Fall back to standalone if Flask context not available
        db = get_database_standalone()
    course_codes = []
    course_texts = []
    embeddings = []
    
    # Try to get from course_embeddings collection first
    embedding_docs = db.course_embeddings.find({"embedding": {"$exists": True}})
    
    for doc in embedding_docs:
        course_code = doc.get('course_code')
        embedding = doc.get('embedding')
        course_text = doc.get('course_text_corpus', '')
        
        if course_code and embedding:
            course_codes.append(course_code)
            course_texts.append(course_text)
            embeddings.append(embedding)
    
    # Also check courses collection for embeddings
    course_docs = db.courses.find({"embedding": {"$exists": True}})
    
    for doc in course_docs:
        subject_code = doc.get('department', '')
        catalog_number = doc.get('catalog_number', '')
        embedding = doc.get('embedding')
        course_text = doc.get('course_text_corpus', '')
        
        if subject_code and catalog_number and embedding:
            course_code = f"{subject_code} {catalog_number}"
            if course_code not in course_codes:  # Avoid duplicates
                course_codes.append(course_code)
                course_texts.append(course_text)
                embeddings.append(embedding)
    
    logging.info(f"Loaded {len(course_codes)} course embeddings from database")
    return course_codes, course_texts, embeddings


def vector_search_courses(
    query_text: str,
    available_course_codes: Optional[List[str]] = None,
    top_k: int = 50,
    model: str = "text-embedding-3-small"
) -> List[Tuple[str, float]]:
    """
    Perform vector search to find semantically similar courses.
    
    Args:
        query_text: The query text (user's request or course description)
        available_course_codes: Optional list of course codes to limit search to
        top_k: Number of top results to return
        model: Embedding model to use
    
    Returns:
        List of tuples (course_code, similarity_score) sorted by similarity
    """
    # Load embeddings from database
    all_course_codes, all_course_texts, all_embeddings = get_course_embeddings_from_db()
    
    if len(all_course_codes) == 0:
        logging.warning("No embeddings found in database. Generating on-the-fly...")
        # Fallback: generate embeddings on-the-fly (slower)
        courses = get_all_courses_with_text()
        if available_course_codes:
            courses = [(code, text, obj) for code, text, obj in courses if code in available_course_codes]
        
        course_codes = [code for code, _, _ in courses]
        course_texts = [text for _, text, _ in courses]
        
        return find_similar_courses(query_text, course_texts, course_codes, top_k=top_k, model=model)
    
    # Filter to available courses if specified
    if available_course_codes:
        filtered_indices = [
            i for i, code in enumerate(all_course_codes)
            if code in available_course_codes
        ]
        course_codes = [all_course_codes[i] for i in filtered_indices]
        course_texts = [all_course_texts[i] for i in filtered_indices]
        embeddings = [all_embeddings[i] for i in filtered_indices]
    else:
        course_codes = all_course_codes
        course_texts = all_course_texts
        embeddings = all_embeddings
    
    if len(course_codes) == 0:
        return []
    
    # Generate embedding for query
    query_embedding = embedding_from_string(query_text, model=model)
    
    # Calculate similarities
    similarities = [cosine_similarity(query_embedding, emb) for emb in embeddings]
    
    # Create list of (course_code, similarity) tuples
    course_similarities = list(zip(course_codes, similarities))
    
    # Sort by similarity (descending)
    course_similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top-k
    return course_similarities[:top_k]


def filter_and_rerank_courses(
    vector_results: List[Tuple[str, float]],
    past_courses: Dict[str, str],
    concentration: Optional[str] = None,
    grade: Optional[str] = None,
    max_level: Optional[int] = None,
    min_similarity: float = 0.0
) -> List[Tuple[str, float]]:
    """
    Filter and rerank vector search results based on constraints.
    
    Args:
        vector_results: List of (course_code, similarity_score) from vector search
        past_courses: Dict of past course codes to grades
        concentration: Major/concentration (department code)
        grade: Class year (e.g., "Freshman", "Sophomore")
        max_level: Maximum course level (e.g., 200 for 200-level max)
        min_similarity: Minimum similarity score to include
    
    Returns:
        Filtered and reranked list of (course_code, final_score)
    """
    filtered = []
    
    for course_code, similarity_score in vector_results:
        # Skip if similarity too low
        if similarity_score < min_similarity:
            continue
        
        # Skip if already taken
        if course_code in past_courses:
            continue
        
        # Extract course level from catalog number
        try:
            catalog_number = course_code.split()[1]
            course_level = int(catalog_number[0]) * 100  # 100, 200, 300, 400
        except (ValueError, IndexError):
            course_level = None
        
        # Filter by max level if specified
        if max_level and course_level and course_level > max_level:
            continue
        
        # Calculate final score (can be adjusted based on personalization)
        final_score = similarity_score
        
        # Boost score if matches concentration
        if concentration:
            subject_code = course_code.split()[0]
            if subject_code.upper() == concentration.upper():
                final_score *= 1.2  # 20% boost
        
        # Adjust based on class year appropriateness
        if grade and course_level:
            if grade.lower() in ["freshman", "first-year"]:
                # Prefer 100-level courses
                if course_level == 100:
                    final_score *= 1.1
                elif course_level >= 300:
                    final_score *= 0.8
            elif grade.lower() in ["sophomore"]:
                # Prefer 200-level courses
                if course_level == 200:
                    final_score *= 1.1
                elif course_level >= 400:
                    final_score *= 0.9
            elif grade.lower() in ["junior", "senior"]:
                # Can handle higher level courses
                if course_level >= 300:
                    final_score *= 1.05
        
        filtered.append((course_code, final_score))
    
    # Rerank by final score
    filtered.sort(key=lambda x: x[1], reverse=True)
    
    return filtered


def build_query_from_student_data(
    student_data: Dict[str, Any],
    user_query: Optional[str] = None
) -> str:
    """
    Build a query text for vector search from student data and optional user query.
    User query takes absolute priority - other factors are only for context.
    
    Args:
        student_data: Dictionary with past_courses, concentration, grade
        user_query: Optional user query text (e.g., "I want a statistics course")
    
    Returns:
        Combined query text for embedding
    """
    query_parts = []
    
    # PRIORITY 1: User query takes absolute priority
    if user_query:
        # Make user query the primary focus
        query_parts.append(user_query)
        query_parts.append("")  # Separator for clarity
    
    # PRIORITY 2: Add context only if it helps with the query
    # For similarity queries, include reference course details
    if user_query:
        query_lower = user_query.lower()
        similarity_keywords = ['similar to', 'like', 'same as', 'equivalent to', 'comparable to', 'related to']
        is_similarity = any(keyword in query_lower for keyword in similarity_keywords)
        
        if is_similarity:
            # For similarity queries, add past courses as context (they might be related)
            past_courses = student_data.get("past_courses", {})
            if past_courses:
                course_codes = list(past_courses.keys())[:2]  # Just 1-2 for context
                query_parts.append(f"Context: Student has taken {', '.join(course_codes)}")
        else:
            # For other queries, add minimal context
            past_courses = student_data.get("past_courses", {})
            if past_courses and len(past_courses) <= 3:
                # Only add if few courses (to avoid diluting the query)
                course_codes = list(past_courses.keys())
                query_parts.append(f"Context: Student has taken: {', '.join(course_codes)}")
    
    # If no user query, create a general query
    if not user_query:
        past_courses = student_data.get("past_courses", {})
        concentration = student_data.get("concentration")
        
        if past_courses:
            course_codes = list(past_courses.keys())
            query_parts.append(f"Student has taken: {', '.join(course_codes)}")
            
            # Add course details for context
            for course_code in list(course_codes)[:3]:  # Limit to 3 most recent
                course_obj = match_course_code(course_code)
                if course_obj:
                    title = course_obj.get('title', '')
                    if title:
                        query_parts.append(f"{course_code}: {title}")
        
        if concentration:
            query_parts.append(f"Major/Concentration: {concentration}")
        
        grade = student_data.get("grade")
        if grade:
            query_parts.append(f"Class year: {grade}")
        
        if past_courses:
            query_parts.append("Recommend courses that build on past coursework")
        elif concentration:
            query_parts.append(f"Recommend foundational courses in {concentration}")
        else:
            query_parts.append("Recommend interesting and relevant courses")
    
    return ". ".join(query_parts)

