import logging
from typing import Dict, Any, Optional
from server.recommendations.course_recommender import (
    get_student_data,
    load_course_details,
    vector_search_courses,
    extract_course_details,
    match_course_code,
    get_courses_by_distribution
)

# System prompt for Tiggy
SYSTEM_PROMPT = """You are Tiggy, an academic advising assistant powered by GPT-4. You are advising Princeton undergraduate students on what courses to consider taking, based on what is offered in the Spring 2026 course catalog. 

You have access to course information from the current term's course catalog. Use the course data provided to recommend courses that match the student's interests, major, class year, and query. 

CRITICAL: Distinguish between SIMILARITY queries, SUBJECT AREA queries, and REQUIREMENT queries (in that priority order):
- SIMILARITY query (HIGHEST PRIORITY): When a student asks for courses "similar to X", "like X", or "related to X" (e.g., "similar to COS 226", "like MAT 201"), they want courses that are semantically similar to the specified course. Use vector embeddings to find similar courses and ONLY recommend those. Ignore distribution requirements, major, and other factors unless explicitly mentioned.
- SUBJECT AREA query: When a student asks for a course in a subject (e.g., "history class", "computer science course", "economics class"), they want courses in that SUBJECT/DEPARTMENT, NOT a distribution requirement. Recommend courses from that department (e.g., "history" → HIS courses, "computer science" → COS courses).
- REQUIREMENT query: When a student explicitly mentions a requirement (e.g., "SEN distribution", "fulfill HA requirement", "need a QCR course", "CD requirement"), they want courses that fulfill that SPECIFIC requirement. For requirement queries, you MUST ONLY recommend courses that have the exact distribution code in their distribution field. DO NOT recommend courses based on semantic similarity, topic relevance, or any other criteria - ONLY exact distribution matches.

When recommending courses:
- Use the course information provided in the context
- For SUBJECT AREA queries: Match courses to the subject/department mentioned (e.g., "history class" → recommend HIS courses, "computer science" → recommend COS courses)
- For REQUIREMENT queries: ONLY recommend courses that have the EXACT distribution code in their distribution field. The system will provide a filtered list - ONLY recommend from that list. DO NOT recommend courses that are not in the filtered list, even if they seem relevant.
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
    context_parts.append('              "detail": {')
    context_parts.append('                "description": "Examines Black Freedom Movement leadership.",')
    context_parts.append('                "distribution": ["LA"]')
    context_parts.append('              },')
    context_parts.append('              "crosslistings": [{"subject": "AMS", "catalog_number": "225"}]')
    context_parts.append('            }')
    context_parts.append('          ]')
    context_parts.append('        }')
    context_parts.append('      ]')
    context_parts.append('    }')
    context_parts.append('  ]')
    context_parts.append('}')
    context_parts.append("")
    context_parts.append("Note: The 'distribution' field in the 'detail' object contains an array of distribution requirement codes.")
    context_parts.append("Valid distribution codes are: LA (Literature and the Arts), SA (Social Analysis), HA (Historical Analysis),")
    context_parts.append("EM (Ethical Thought and Moral Values), EC (Epistemology and Cognition), QR (Quantitative and Computational Reasoning),")
    context_parts.append("STN (Science and Engineering No Lab), STL (Science and Engineering with Laboratory).")
    context_parts.append("A course may have multiple distribution requirements (e.g., ['CD', 'LA']).")
    context_parts.append("")
    
    # Detect if query is about a specific requirement (distribution, prerequisite, etc.)
    query_lower = user_query.lower()
    is_requirement_query = False
    requirement_type = None
    is_similarity_query = False
    similarity_course_code = None
    
    # FIRST PRIORITY: Check if this is a similarity query (e.g., "similar to COS 226", "like COS 226")
    # These take absolute priority over everything else
    similarity_keywords = ['similar to', 'like', 'same as', 'equivalent to', 'comparable to', 'related to']
    for keyword in similarity_keywords:
        if keyword in query_lower:
            # Try to extract course code (e.g., "COS 226", "COS226")
            import re
            # Pattern: 3 letters, optional space, 3 digits
            course_pattern = r'\b([A-Z]{2,4})\s*(\d{3})\b'
            matches = re.findall(course_pattern, user_query.upper())
            if matches:
                is_similarity_query = True
                subject, number = matches[0]
                similarity_course_code = f"{subject} {number}"
                break
    
    # Second, check if this is a subject area query (these take priority over requirement queries)
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
    
    # Only check for requirement keywords if this is NOT a similarity query and NOT a subject area query
    # Similarity queries take absolute priority, then subject area queries, then requirement queries
    if not is_similarity_query and not is_subject_query:
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
    
    # Requirement descriptions for vector search
    requirement_descriptions = {
        'CD (Culture and Difference)': 'Course examining culture and difference, diversity, identity, social differences, cultural perspectives, intersectionality',
        'EC (Epistemology and Cognition)': 'Course on epistemology and cognition, knowledge, thinking, reasoning, philosophy of mind, cognitive science',
        'EM (Ethical Thought and Moral Values)': 'Course on ethical thought and moral values, ethics, morality, philosophy, values, moral reasoning',
        'HA (Historical Analysis)': 'Course in historical analysis, history, historical methods, past events, historical context, historical perspective',
        'LA (Literature and the Arts)': 'Course in literature and the arts, creative arts, literary analysis, artistic expression, cultural production',
        'QCR (Quantitative and Computational Reasoning)': 'Course in quantitative and computational reasoning, mathematics, statistics, data analysis, computational methods, quantitative methods',
        'SEL (Science and Engineering with Laboratory)': 'Science and engineering course with laboratory component, hands-on experiments, lab work, scientific methods',
        'SEN (Science and Engineering No Lab)': 'Science and engineering course without laboratory, theoretical science, mathematical science, computational science',
        'SA (Social Analysis)': 'Course in social analysis, social sciences, society, social structures, social behavior, social institutions, social research'
    }
    
    # If this is a requirement query, use simple lookup from distribution mapping
    if is_requirement_query and requirement_type:
        context_parts.append(f"REQUIREMENT QUERY DETECTED: {requirement_type}")
        context_parts.append("")
        
        # Extract distribution code from requirement type (e.g., "SEL (Science...)" -> "SEL")
        import re
        code_match = re.match(r'^([A-Z]{2,4})\s*\(', requirement_type)
        
        if code_match:
            requirement_code = code_match.group(1).upper()
            
            # Handle special cases and normalize codes
            distribution_code_mapping = {
                'STL': 'SEL',
                'STN': 'SEN',
                'QR': 'QCR'
            }
            normalized_code = distribution_code_mapping.get(requirement_code, requirement_code)
            
            # Simple lookup: get all courses with this distribution code
            matching_courses = get_courses_by_distribution(
                distribution_code=normalized_code,
                past_courses=past_courses,
                exclude_taken=True
            )
            
            # For SEN/SEL, use vector search to prioritize science-focused courses
            if normalized_code in ['SEN', 'SEL'] and matching_courses:
                try:
                    # Build a query for science courses
                    if normalized_code == 'SEL':
                        science_query = "Science and engineering course with laboratory component, lab work, experiments, scientific methods"
                    else:  # SEN
                        science_query = "Science and engineering course without laboratory, theoretical science, mathematical science, computational science"
                    
                    # Do vector search within matching courses to prioritize science-focused ones
                    vector_results = vector_search_courses(
                        query_text=science_query,
                        available_course_codes=matching_courses,
                        top_k=min(50, len(matching_courses))
                    )
                    
                    if vector_results:
                        # Reorder: science-focused courses first, then the rest
                        vector_course_codes = [code for code, _ in vector_results]
                        prioritized = [code for code in vector_course_codes if code in matching_courses]
                        remaining = [code for code in matching_courses if code not in vector_course_codes]
                        matching_courses = prioritized + remaining
                        logging.info(f"Prioritized {len(prioritized)} science-focused courses out of {len(matching_courses)} total")
                except Exception as e:
                    logging.warning(f"Vector search for science courses failed: {e}")
                    # Continue with original order
            
            # Display matching courses
            if matching_courses:
                context_parts.append("COURSES THAT FULFILL {} (found {} courses with exact distribution match):".format(requirement_type, len(matching_courses)))
                context_parts.append("")
                context_parts.append(f"IMPORTANT: ALL courses listed below have been verified to have '{normalized_code}' in their distribution field.")
                context_parts.append(f"These are the ONLY courses that fulfill {requirement_type}. DO NOT recommend any other courses.")
                context_parts.append("")
                
                # Limit to top 30 courses for display (to avoid token limits)
                display_limit = 30
                for course_code in matching_courses[:display_limit]:
                    course_details = extract_course_details(course_code)
                    if course_details:
                        # Verify and show the distribution field
                        course_obj = match_course_code(course_code)
                        distribution_display = "Not found"
                        if course_obj:
                            detail = course_obj.get('detail', {})
                            distribution = detail.get('distribution', '')
                            if distribution:
                                if isinstance(distribution, list):
                                    distribution_display = ', '.join(distribution)
                                else:
                                    distribution_display = str(distribution)
                        
                        context_parts.append(f"{course_code} - {course_details.get('title', '')}")
                        context_parts.append(f"  Distribution: {distribution_display} ✓")
                        context_parts.append(f"  Instructor: {course_details.get('instructor', 'TBA')}")
                        context_parts.append(f"  Format: {course_details.get('format', 'Unknown')}")
                        context_parts.append(f"  Schedule: {course_details.get('schedule', 'TBA')}")
                        if course_details.get('description'):
                            context_parts.append(f"  Description: {course_details.get('description', '')[:200]}...")
                        context_parts.append("")
                
                if len(matching_courses) > display_limit:
                    context_parts.append(f"(Showing {display_limit} of {len(matching_courses)} courses that fulfill this requirement)")
                    context_parts.append("")
            else:
                context_parts.append(f"No courses found that fulfill {requirement_type}.")
                context_parts.append("This may indicate that:")
                context_parts.append("1. The distribution code may be different in the data")
                context_parts.append("2. No courses are offered with this requirement in Spring 2026")
                context_parts.append("3. All matching courses have already been taken")
                context_parts.append("")
        else:
            # Generic requirement query (e.g., "distribution requirement" without specific code)
            context_parts.append("Generic requirement query detected. Please specify a specific distribution requirement (e.g., SEL, SEN, HA, LA, etc.)")
            context_parts.append("")
    
    # If this is a similarity query, use vector search to find similar courses
    if is_similarity_query and similarity_course_code:
        context_parts.append(f"SIMILARITY QUERY DETECTED: Finding courses similar to {similarity_course_code}")
        context_parts.append("")
        
        # Get the course details for the reference course
        reference_course = match_course_code(similarity_course_code)
        if reference_course:
            ref_title = reference_course.get('title', '')
            ref_description = reference_course.get('detail', {}).get('description', '')
            context_parts.append(f"Reference course: {similarity_course_code} - {ref_title}")
            if ref_description:
                context_parts.append(f"Description: {ref_description[:200]}...")
            context_parts.append("")
        
        # Use vector search to find similar courses
        try:
            # Build query text focusing on the similarity request
            similarity_query = f"Course similar to {similarity_course_code}. {user_query}"
            vector_results = vector_search_courses(
                query_text=similarity_query,
                available_course_codes=None,  # Search all courses
                top_k=20
            )
            
            if vector_results:
                context_parts.append("COURSES SIMILAR TO {} (found using semantic search):".format(similarity_course_code))
                context_parts.append("")
                
                for course_code, similarity_score in vector_results[:15]:  # Top 15 most similar
                    # Skip the reference course itself
                    if course_code.upper() == similarity_course_code.upper():
                        continue
                    
                    course_details = extract_course_details(course_code)
                    if course_details:
                        context_parts.append(f"{course_code} - {course_details.get('title', '')}")
                        context_parts.append(f"  Instructor: {course_details.get('instructor', 'TBA')}")
                        context_parts.append(f"  Format: {course_details.get('format', 'Unknown')}")
                        context_parts.append(f"  Schedule: {course_details.get('schedule', 'TBA')}")
                        if course_details.get('description'):
                            context_parts.append(f"  Description: {course_details.get('description', '')[:200]}...")
                        context_parts.append(f"  Similarity Score: {similarity_score:.3f}")
                        context_parts.append("")
        except Exception as e:
            logging.warning(f"Vector search failed, falling back to regular search: {e}")
            context_parts.append("(Note: Using regular course search as fallback)")
            context_parts.append("")
    
    # Include a comprehensive list of available courses
    # For requirement queries, skip showing all courses - only show the filtered matches above
    if not is_requirement_query:
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
    
    # Add similarity query instructions (HIGHEST PRIORITY)
    if is_similarity_query and similarity_course_code:
        context_parts.append(f"CRITICAL: The student is asking for courses SIMILAR TO {similarity_course_code}.")
        context_parts.append("")
        context_parts.append("SIMILARITY QUERY RULES (MUST FOLLOW - HIGHEST PRIORITY):")
        context_parts.append("1. ONLY recommend courses that are semantically similar to the reference course.")
        context_parts.append("2. The courses listed above have been pre-selected using vector embeddings for semantic similarity.")
        context_parts.append("3. DO NOT recommend courses based on:")
        context_parts.append("   - Distribution requirements (unless explicitly mentioned)")
        context_parts.append("   - The student's major (unless it happens to align)")
        context_parts.append("   - Other criteria that don't relate to similarity")
        context_parts.append("4. Focus on courses that:")
        context_parts.append("   - Cover similar topics or subject matter")
        context_parts.append("   - Have similar prerequisites or difficulty level")
        context_parts.append("   - Are in related departments or cross-listed")
        context_parts.append("5. If the student mentions additional criteria (e.g., 'similar to COS 226 but with more statistics'),")
        context_parts.append("   prioritize courses that match BOTH the similarity AND the additional criteria.")
        context_parts.append("6. The similarity score indicates how semantically similar each course is (higher = more similar).")
        context_parts.append("")
        context_parts.append("Recommend 3-5 courses from the similarity search results above.")
        context_parts.append("For each course, explain WHY it's similar to the reference course.")
        context_parts.append("")
    # Add requirement-specific instructions if detected (but only if not a similarity query)
    elif is_requirement_query:
        # Extract the distribution code for the instructions
        import re
        code_match = re.match(r'^([A-Z]{2,4})\s*\(', requirement_type)
        dist_code = code_match.group(1).upper() if code_match else "REQUIREMENT"
        
        context_parts.append(f"CRITICAL: The student is asking about fulfilling a {requirement_type}.")
        context_parts.append("")
        context_parts.append("REQUIREMENT-SPECIFIC RULES (MUST FOLLOW - NO EXCEPTIONS):")
        context_parts.append(f"1. The courses listed above have been DIRECTLY FILTERED from the course catalog.")
        context_parts.append(f"2. These courses have been verified to have '{dist_code}' in their distribution field.")
        context_parts.append(f"3. YOU MUST ONLY recommend courses from the list above that have '{dist_code}' in their distribution field.")
        context_parts.append(f"4. DO NOT recommend ANY course that does NOT have '{dist_code}' in its distribution field, even if:")
        context_parts.append("   - It seems related to the requirement topic")
        context_parts.append("   - It's in the student's major")
        context_parts.append("   - It's otherwise interesting or relevant")
        context_parts.append("   - It has a similar description")
        context_parts.append(f"5. If a course is listed above, it has been verified to fulfill {requirement_type}.")
        context_parts.append(f"6. If a course is NOT listed above, it does NOT fulfill {requirement_type} - DO NOT recommend it.")
        context_parts.append("7. The student's major, interests, and other factors are IRRELEVANT - only exact distribution matches count.")
        context_parts.append("8. You may select from the courses listed above based on other factors (schedule, instructor, etc.),")
        context_parts.append(f"   but you MUST ONLY choose from courses that have '{dist_code}' in their distribution field.")
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
        context_parts.append("- PRIORITIZE the student's explicit query over their major or other factors")
        context_parts.append("- Consider the student's class year for appropriate course levels")
        context_parts.append("- Consider their major for relevant courses ONLY as a secondary factor")
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

