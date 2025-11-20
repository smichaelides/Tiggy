import os
import json
import logging
import random
from typing import Dict, List, Optional, Any
from bson import ObjectId
from server.database import get_database

# Cache for course details JSON
_course_details_cache: Optional[Dict[str, Any]] = None
_major_requirements_cache: Optional[Dict[str, Any]] = None


def _get_course_details_path() -> str:
    """Get the absolute path to spring26_course_details.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '..', 'data', 'course_info', 'spring26_course_details.json')


def _get_major_requirements_path() -> str:
    """Get the absolute path to all_major_requirements.json"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, '..', 'data', 'course_info', 'all_major_requirements.json')


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


def build_recommendation_prompt(
    student_data: Dict[str, Any],
    available_courses: List[str]
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
- Use their past classes and grade received in class (if given) to recommend courses of appropriate difficulty"""

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

