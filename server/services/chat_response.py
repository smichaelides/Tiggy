import logging
from typing import Dict, Any, Optional
from server.services.course_recommender import (
    get_student_data,
    load_course_details
)

# System prompt for Tiggy
SYSTEM_PROMPT = """You are Tiggy, an academic advising assistant powered by GPT-4. You are advising Princeton undergraduate students on what courses to consider taking, based on what is offered in the Spring 2026 course catalog. 

You have access to course information from the current term's course catalog. Use the course data provided to recommend courses that match the student's interests, major, class year, and query. 

CRITICAL: Distinguish between SUBJECT AREA queries and REQUIREMENT queries:
- SUBJECT AREA query: When a student asks for a course in a subject (e.g., "history class", "computer science course", "economics class"), they want courses in that SUBJECT/DEPARTMENT, NOT a distribution requirement. Recommend courses from that department (e.g., "history" → HIS courses, "computer science" → COS courses).
- REQUIREMENT query: When a student explicitly mentions a requirement (e.g., "SEN distribution", "fulfill HA requirement", "need a QCR course"), they want courses that fulfill that SPECIFIC requirement.

When recommending courses:
- Use the course information provided in the context
- For SUBJECT AREA queries: Match courses to the subject/department mentioned (e.g., "history class" → recommend HIS courses, "computer science" → recommend COS courses)
- For REQUIREMENT queries: ONLY recommend courses that actually fulfill the specified requirement
- Consider the student's class year for appropriate course levels
- Consider their major for relevant courses ONLY when it doesn't conflict with a specific requirement query
- If you see relevant courses in the provided data, recommend them with confidence
- Always explain your reasoning
- If you cannot find relevant courses in the provided data, you can acknowledge that and suggest they check the full course catalog or contact their advisor"""

# returns tuple of system prompt and contex message
def build_chat_prompt(
    user_id: str,
    user_query: str
) -> tuple[str, str]:
    # Get student data
    student_data = get_student_data(user_id)
    major = student_data.get("concentration")
    class_year = student_data.get("grade")
    past_courses = student_data.get("past_courses", {})
    
    # Load course details
    course_details = load_course_details()
    
    # Build context message
    context_parts = []
    
    context_parts.append("You are provided with course information from the following sources:")
    context_parts.append("- all_major_requirements.json - gives all the requirements and info on each major")
    context_parts.append("- course_codes.json - outlines the course codes")
    context_parts.append("- departmentals.json - outlines the specific departments")
    context_parts.append("- spring26_course_details.json - current term's course catalog")
    context_parts.append("")
    
    context_parts.append("STUDENT INFORMATION:")
    if major:
        context_parts.append(f"Major: {major}")
    else:
        context_parts.append("Major: Not specified")
    
    if class_year:
        context_parts.append(f"Class: {class_year}")
    else:
        context_parts.append("Class: Not specified")
    
    if past_courses:
        context_parts.append("Past courses taken:")
        for course_code, grade in past_courses.items():
            context_parts.append(f"  - {course_code}: {grade}")
    else:
        context_parts.append("Past courses: None")
    context_parts.append("")
    
    context_parts.append("CURRENT TERM COURSE CATALOG:")
    context_parts.append("The course catalog structure is as follows:")
    context_parts.append('{')
    context_parts.append('  "term": [')
    context_parts.append('    {')
    context_parts.append('      "code": "1264",')
    context_parts.append('      "suffix": "S2026",')
    context_parts.append('      "cal_name": "Spring 2026",')
    context_parts.append('      "subjects": [')
    context_parts.append('        {')
    context_parts.append('          "code": "AAS",')
    context_parts.append('          "name": "African American Studies",')
    context_parts.append('          "courses": [')
    context_parts.append('            {')
    context_parts.append('              "catalog_number": "225",')
    context_parts.append('              "title": "Martin, Malcolm, and Ella",')
    context_parts.append('              "instructors": [{"full_name": "Eddie S. Glaude"}],')
    context_parts.append('              "classes": [{"type_name": "Seminar"}],')
    context_parts.append('              "detail": {"description": "Examines Black Freedom Movement leadership."},')
    context_parts.append('              "crosslistings": [{"subject": "AMS", "catalog_number": "225"}]')
    context_parts.append('            }')
    context_parts.append('          ]')
    context_parts.append('        }')
    context_parts.append('      ]')
    context_parts.append('    }')
    context_parts.append('  ]')
    context_parts.append('}')
    context_parts.append("")
    
    # Detect if query is about a specific requirement (distribution, prerequisite, etc.)
    query_lower = user_query.lower()
    is_requirement_query = False
    requirement_type = None
    
    # First, check if this is a subject area query (these take priority over requirement queries)
    # Map common subject mentions to department codes
    dept_keywords = {
        'computer science': ['COS'],
        'cs': ['COS'],
        'programming': ['COS'],
        'economics': ['ECO'],
        'history': ['HIS'],
        'philosophy': ['PHI'],
        'math': ['MAT'],
        'mathematics': ['MAT'],
        'physics': ['PHY'],
        'chemistry': ['CHM'],
        'biology': ['MOL', 'EEB'],
        'english': ['ENG'],
        'literature': ['ENG'],
        'politics': ['POL'],
        'political science': ['POL'],
        'psychology': ['PSY'],
        'sociology': ['SOC'],
        'art': ['ART', 'VIS'],
        'music': ['MUS'],
        'theater': ['THR'],
    }
    
    # Check if query mentions a subject area (e.g., "history class", "computer science course")
    is_subject_query = False
    for keyword in dept_keywords.keys():
        if keyword in query_lower:
            is_subject_query = True
            break
    
    # Check for distribution requirement mentions (only if not a subject query)
    distribution_keywords = {
        # Culture and Difference
        'cd': 'CD (Culture and Difference)',
        'culture and difference': 'CD (Culture and Difference)',
        # Epistemology and Cognition
        'ec': 'EC (Epistemology and Cognition)',
        'epistemology and cognition': 'EC (Epistemology and Cognition)',
        'epistemology': 'EC (Epistemology and Cognition)',
        'cognition': 'EC (Epistemology and Cognition)',
        # Ethical Thought and Moral Values
        'em': 'EM (Ethical Thought and Moral Values)',
        'ethical thought and moral values': 'EM (Ethical Thought and Moral Values)',
        'ethical thought': 'EM (Ethical Thought and Moral Values)',
        'moral values': 'EM (Ethical Thought and Moral Values)',
        'ethics': 'EM (Ethical Thought and Moral Values)',
        # Historical Analysis
        'ha': 'HA (Historical Analysis)',
        'historical analysis': 'HA (Historical Analysis)',
        # Literature and the Arts
        'la': 'LA (Literature and the Arts)',
        'literature and the arts': 'LA (Literature and the Arts)',
        'literature and arts': 'LA (Literature and the Arts)',
        # Quantitative and Computational Reasoning
        'qcr': 'QCR (Quantitative and Computational Reasoning)',
        'quantitative and computational reasoning': 'QCR (Quantitative and Computational Reasoning)',
        'quantitative reasoning': 'QCR (Quantitative and Computational Reasoning)',
        'computational reasoning': 'QCR (Quantitative and Computational Reasoning)',
        # Science and Engineering with Laboratory
        'sel': 'SEL (Science and Engineering with Laboratory)',
        'science and engineering with lab': 'SEL (Science and Engineering with Laboratory)',
        'science and engineering with laboratory': 'SEL (Science and Engineering with Laboratory)',
        'science with lab': 'SEL (Science and Engineering with Laboratory)',
        'science with laboratory': 'SEL (Science and Engineering with Laboratory)',
        # Science and Engineering No Lab
        'sen': 'SEN (Science and Engineering No Lab)',
        'science and engineering no lab': 'SEN (Science and Engineering No Lab)',
        'science no lab': 'SEN (Science and Engineering No Lab)',
        'science without lab': 'SEN (Science and Engineering No Lab)',
        'science without laboratory': 'SEN (Science and Engineering No Lab)',
        # Social Analysis
        'sa': 'SA (Social Analysis)',
        'social analysis': 'SA (Social Analysis)',
        # General requirement keywords
        'distribution': 'distribution requirement',
        'distribution requirement': 'distribution requirement',
        'fulfill': 'requirement',
        'requirement': 'requirement',
        'prerequisite': 'prerequisite',
        'prereq': 'prerequisite',
    }
    
    # Only check for requirement keywords if this is NOT a subject area query
    # Subject area queries (e.g., "history class") take priority over requirement queries
    if not is_subject_query:
        for keyword, req_type in distribution_keywords.items():
            if keyword in query_lower:
                is_requirement_query = True
                requirement_type = req_type
                break
    
    # Determine relevant departments based on query and major
    relevant_departments = []
    
    # Find relevant departments from query (only if not a requirement query)
    if not is_requirement_query:
        for keyword, depts in dept_keywords.items():
            if keyword in query_lower:
                relevant_departments.extend(depts)
    
    # Add student's major department if available (but only if not a requirement query)
    # For requirement queries, we want courses from ALL departments that fulfill the requirement
    if major and not is_requirement_query:
        relevant_departments.append(major.upper())
    
    # Remove duplicates and ensure we have some departments
    relevant_departments = list(set(relevant_departments))
    
    # Include a comprehensive list of available courses
    context_parts.append("AVAILABLE COURSES (Spring 2026):")
    if 'term' in course_details and course_details['term']:
        term = course_details['term'][0]
        course_count = 0
        
        # For requirement queries, include courses from ALL departments (not just major)
        # For regular queries, focus on relevant departments
        if is_requirement_query:
            context_parts.append(f"⚠️ REQUIREMENT QUERY DETECTED: {requirement_type}")
            context_parts.append("Including courses from ALL departments that may fulfill this requirement.")
            context_parts.append("")
            # Include courses from all departments, but prioritize those that might fulfill the requirement
            for subject_obj in term.get('subjects', []):
                subject_code = subject_obj.get('code', '').upper()
                subject_name = subject_obj.get('name', '')
                context_parts.append(f"=== {subject_code} - {subject_name} ===")
                for course in subject_obj.get('courses', []):
                    catalog_num = course.get('catalog_number', '')
                    title = course.get('title', '')
                    instructors = course.get('instructors', [])
                    instructor_name = instructors[0].get('full_name', 'TBA') if instructors else 'TBA'
                    classes = course.get('classes', [])
                    format_type = classes[0].get('type_name', 'Unknown') if classes else 'Unknown'
                    detail = course.get('detail', {})
                    description = detail.get('description', '')[:300] if detail else ''
                    
                    # Format schedule
                    schedule = "TBA"
                    if classes and len(classes) > 0:
                        class_schedule = classes[0].get('schedule', {})
                        meetings = class_schedule.get('meetings', [])
                        if meetings:
                            schedule_parts = []
                            for meeting in meetings:
                                days = meeting.get('days', [])
                                start_time = meeting.get('start_time', '')
                                end_time = meeting.get('end_time', '')
                                if days and start_time and end_time:
                                    day_map = {'M': 'Mon', 'T': 'Tue', 'W': 'Wed', 'R': 'Thu', 'F': 'Fri', 'S': 'Sat', 'U': 'Sun'}
                                    days_str = ', '.join([day_map.get(day, day) for day in days])
                                    schedule_parts.append(f"{days_str} {start_time}-{end_time}")
                            if schedule_parts:
                                schedule = ' | '.join(schedule_parts)
                    
                    context_parts.append(f"{subject_code} {catalog_num} - {title}")
                    context_parts.append(f"  Instructor: {instructor_name}")
                    context_parts.append(f"  Format: {format_type}")
                    context_parts.append(f"  Schedule: {schedule}")
                    if description:
                        context_parts.append(f"  Description: {description}")
                    context_parts.append("")
                    course_count += 1
                    if course_count >= 200:  # Limit for requirement queries to avoid token limits
                        break
                if course_count >= 200:
                    break
        else:
            # First, include all courses from relevant departments
            if relevant_departments:
                context_parts.append(f"Relevant departments based on query: {', '.join(relevant_departments)}")
                context_parts.append("")
                for subject_obj in term.get('subjects', []):
                    subject_code = subject_obj.get('code', '').upper()
                    if subject_code in relevant_departments:
                        subject_name = subject_obj.get('name', '')
                        context_parts.append(f"=== {subject_code} - {subject_name} ===")
                        for course in subject_obj.get('courses', []):
                            catalog_num = course.get('catalog_number', '')
                            title = course.get('title', '')
                            instructors = course.get('instructors', [])
                            instructor_name = instructors[0].get('full_name', 'TBA') if instructors else 'TBA'
                            classes = course.get('classes', [])
                            format_type = classes[0].get('type_name', 'Unknown') if classes else 'Unknown'
                            detail = course.get('detail', {})
                            description = detail.get('description', '')[:300] if detail else ''
                            
                            # Format schedule
                            schedule = "TBA"
                            if classes and len(classes) > 0:
                                class_schedule = classes[0].get('schedule', {})
                                meetings = class_schedule.get('meetings', [])
                                if meetings:
                                    schedule_parts = []
                                    for meeting in meetings:
                                        days = meeting.get('days', [])
                                        start_time = meeting.get('start_time', '')
                                        end_time = meeting.get('end_time', '')
                                        if days and start_time and end_time:
                                            day_map = {'M': 'Mon', 'T': 'Tue', 'W': 'Wed', 'R': 'Thu', 'F': 'Fri', 'S': 'Sat', 'U': 'Sun'}
                                            days_str = ', '.join([day_map.get(day, day) for day in days])
                                            schedule_parts.append(f"{days_str} {start_time}-{end_time}")
                                    if schedule_parts:
                                        schedule = ' | '.join(schedule_parts)
                            
                            context_parts.append(f"{subject_code} {catalog_num} - {title}")
                            context_parts.append(f"  Instructor: {instructor_name}")
                            context_parts.append(f"  Format: {format_type}")
                            context_parts.append(f"  Schedule: {schedule}")
                            if description:
                                context_parts.append(f"  Description: {description}")
                            context_parts.append("")
                            course_count += 1
                        context_parts.append("")
            
            # If no relevant departments found or we need more courses, include a broader sample
            if course_count < 20 or not relevant_departments:
                context_parts.append("=== Additional Courses from Other Departments ===")
                added_count = 0
                for subject_obj in term.get('subjects', []):
                    subject_code = subject_obj.get('code', '').upper()
                    if relevant_departments and subject_code in relevant_departments:
                        continue  # Skip, already added
                    
                    subject_name = subject_obj.get('name', '')
                    for course in subject_obj.get('courses', [])[:3]:  # Limit to 3 per department
                        catalog_num = course.get('catalog_number', '')
                        title = course.get('title', '')
                        instructors = course.get('instructors', [])
                        instructor_name = instructors[0].get('full_name', 'TBA') if instructors else 'TBA'
                        classes = course.get('classes', [])
                        format_type = classes[0].get('type_name', 'Unknown') if classes else 'Unknown'
                        detail = course.get('detail', {})
                        description = detail.get('description', '')[:200] if detail else ''
                        
                        context_parts.append(f"{subject_code} {catalog_num} - {title}")
                        context_parts.append(f"  Instructor: {instructor_name}")
                        context_parts.append(f"  Format: {format_type}")
                        if description:
                            context_parts.append(f"  Description: {description}...")
                        context_parts.append("")
                        added_count += 1
                        if added_count >= 30:  # Limit additional courses
                            break
                    if added_count >= 30:
                        break
    context_parts.append("")
    
    context_parts.append("INSTRUCTIONS:")
    
    # Add requirement-specific instructions if detected
    if is_requirement_query:
        context_parts.append(f"CRITICAL: The student is asking about fulfilling a {requirement_type}.")
        context_parts.append("")
        context_parts.append("REQUIREMENT-SPECIFIC RULES (MUST FOLLOW):")
        context_parts.append("1. ONLY recommend courses that actually fulfill the requested requirement.")
        context_parts.append("2. DO NOT recommend courses that do NOT fulfill the requirement, even if they are:")
        context_parts.append("   - In the student's major")
        context_parts.append("   - Related to the subject area")
        context_parts.append("   - Otherwise interesting or relevant")
        context_parts.append("3. If you cannot determine which courses fulfill the requirement from the provided data,")
        context_parts.append("   you must state that you need more information about which courses fulfill this requirement.")
        context_parts.append("4. The student's major is SECONDARY - the requirement fulfillment is MANDATORY.")
        context_parts.append("5. If the student has a major, you can prefer courses that both fulfill the requirement AND are relevant to their major,")
        context_parts.append("   but requirement fulfillment is the primary criterion.")
        context_parts.append("")
        context_parts.append("For distribution requirements:")
        context_parts.append("- CD (Culture and Difference): One course examining culture and difference")
        context_parts.append("- EC (Epistemology and Cognition): One course on epistemology and cognition")
        context_parts.append("- EM (Ethical Thought and Moral Values): One course on ethical thought and moral values")
        context_parts.append("- HA (Historical Analysis): One course in historical analysis")
        context_parts.append("- LA (Literature and the Arts): Two courses in literature and the arts")
        context_parts.append("- QCR (Quantitative and Computational Reasoning): One course in quantitative and computational reasoning")
        context_parts.append("- SEL (Science and Engineering with Laboratory): At least one course with laboratory component (part of two-course requirement)")
        context_parts.append("- SEN (Science and Engineering No Lab): Can be the second course in the science requirement (if not taking a second SEL)")
        context_parts.append("- SA (Social Analysis): Two courses in social analysis")
        context_parts.append("")
    else:
        context_parts.append("Based on the student's query below, recommend relevant courses from the available courses listed above.")
        context_parts.append("")
        context_parts.append("IMPORTANT: This is a SUBJECT AREA query, NOT a requirement query.")
        context_parts.append("The student is asking for courses in a specific subject/department (e.g., 'history class', 'computer science course').")
        context_parts.append("DO NOT interpret this as a distribution requirement query.")
        context_parts.append("")
        context_parts.append("When recommending:")
        context_parts.append("- Match courses to the SUBJECT/DEPARTMENT the student mentioned (e.g., 'history class' → recommend HIS courses, 'computer science' → recommend COS courses)")
        context_parts.append("- Do NOT assume they want a distribution requirement unless they explicitly mention one")
        context_parts.append("- Consider the student's class year for appropriate course levels")
        context_parts.append("- Consider their major for relevant courses")
        context_parts.append("- Recommend 3-5 courses that best match their query")
        context_parts.append("- For each course, provide: course code, title, instructor, format, schedule, and a brief rationale")
        context_parts.append("- If the student asks a general question, provide helpful recommendations from the available courses")
        context_parts.append("")
    
    context_parts.append("STUDENT QUERY:")
    context_parts.append(user_query)
    context_parts.append("")
    context_parts.append("Please provide course recommendations based on the student's query and the available courses listed above.")
    
    context_message = "\n".join(context_parts)
    
    return SYSTEM_PROMPT, context_message

