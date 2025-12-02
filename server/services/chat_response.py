import logging
from typing import Dict, Any, Optional
from server.services.course_recommender import (
    get_student_data,
    load_course_details
)

# System prompt for Tiggy
SYSTEM_PROMPT = """You are Tiggy, an academic advising assistant powered by GPT-4. You are advising Princeton undergraduate students on what courses to consider taking, based on what is offered in the Spring 2026 course catalog. 

You have access to course information from the current term's course catalog. Use the course data provided to recommend courses that match the student's interests, major, class year, and query. 

When recommending courses:
- Use the course information provided in the context
- Match courses to the student's query (e.g., if they ask about computer science, recommend COS courses)
- Consider the student's class year for appropriate course levels
- Consider their major for relevant courses
- If you see relevant courses in the provided data, recommend them with confidence
- If the student asks about a subject area, look for courses in that department (e.g., "computer science" → COS, "economics" → ECO, "history" → HIS)
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
    
    # Determine relevant departments based on query and major
    relevant_departments = []
    query_lower = user_query.lower()
    
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
    
    # Find relevant departments from query
    for keyword, depts in dept_keywords.items():
        if keyword in query_lower:
            relevant_departments.extend(depts)
    
    # Add student's major department if available
    if major:
        relevant_departments.append(major.upper())
    
    # Remove duplicates and ensure we have some departments
    relevant_departments = list(set(relevant_departments))
    
    # Include a comprehensive list of available courses
    context_parts.append("AVAILABLE COURSES (Spring 2026):")
    if 'term' in course_details and course_details['term']:
        term = course_details['term'][0]
        course_count = 0
        
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
    context_parts.append("Based on the student's query below, recommend relevant courses from the available courses listed above.")
    context_parts.append("")
    context_parts.append("When recommending:")
    context_parts.append("- Match courses to what the student is asking for (e.g., 'computer science' → COS courses)")
    context_parts.append("- Consider the student's class year for appropriate course levels")
    context_parts.append("- Consider their major for additional relevant courses")
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

