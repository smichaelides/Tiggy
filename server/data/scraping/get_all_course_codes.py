#!/usr/bin/env python3
"""
get_all_course_codes.py
Fetches all unique course codes from the past 4 years of Princeton courses.
Returns a simple JSON array of course codes (e.g., ["COS234", "MAT201", ...])
"""

import sys
import os
import json
from datetime import datetime
from typing import Set

# Add the scraping directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from studentapp import StudentApp


def get_past_4_years_terms(studentapp: StudentApp) -> list:
    """
    Get the 8 most recent terms (4 years, 2 semesters per year).
    Uses the most recent term and works backwards.
    Term codes are in format: YYSS where YY is year and SS is semester
    Pattern: Spring terms end in 2, Fall terms end in 4 (e.g., 1262=Spring 2024, 1264=Fall 2024)
    """
    terms_data = studentapp.get_terms()
    
    if 'term' not in terms_data or len(terms_data['term']) == 0:
        return []
    
    # Get most recent term code
    most_recent_term = str(terms_data['term'][0]['code'])
    
    if len(most_recent_term) != 4:
        return []
    
    # Extract year (first 2 digits) and semester (last 2 digits)
    year_part = int(most_recent_term[:2])
    semester_part = int(most_recent_term[2:])
    
    # Generate 8 most recent terms (4 years = 8 semesters)
    # Working backwards from most recent
    # Pattern: Spring terms end in 2, Fall terms end in 4
    recent_terms = []
    
    current_year = year_part
    current_semester = semester_part
    
    for i in range(8):
        term_code = f"{current_year:02d}{current_semester:02d}"
        recent_terms.append(term_code)
        
        # Move to previous semester
        # If Fall (ends in 4), go to Spring of same year (ends in 2)
        # If Spring (ends in 2), go to Fall of previous year (ends in 4)
        if current_semester % 10 == 4:  # Fall -> Spring (same year)
            current_semester = current_semester - 2
        else:  # Spring -> Fall (previous year)
            current_semester = current_semester + 2
            current_year -= 1
    
    # Now we need to get the full term objects from the API response
    # Create a mapping of term codes to term objects
    term_map = {}
    for term in terms_data['term']:
        term_code = str(term['code'])
        term_map[term_code] = term
    
    # Return term objects in reverse chronological order (most recent first)
    result_terms = []
    for term_code in recent_terms:
        if term_code in term_map:
            result_terms.append(term_map[term_code])
        else:
            # If term not found, create a minimal term object with just the code
            result_terms.append({'code': term_code, 'cal_name': f'Term {term_code}'})
    
    return result_terms


def extract_course_codes(course_data: dict) -> Set[str]:
    """
    Extract course codes from API response.
    Course codes are in format: DEPTCATNUM (e.g., "COS234")
    """
    course_codes = set()
    
    if 'term' not in course_data:
        return course_codes
    
    for term in course_data['term']:
        for subject in term.get('subjects', []):
            subject_code = subject.get('code', '')
            
            for course in subject.get('courses', []):
                catalog_number = course.get('catalog_number', '')
                
                # Skip if missing required fields
                if not subject_code or not catalog_number:
                    continue
                
                # Format: DEPTCATNUM (e.g., "COS234")
                course_code = f"{subject_code}{catalog_number}"
                course_codes.add(course_code)
    
    return course_codes


def get_all_course_codes() -> list:
    """
    Main function to get all unique course codes from past 4 years.
    Returns a sorted list of course codes.
    """
    studentapp = StudentApp()
    
    # Get all terms from past 4 years
    terms = get_past_4_years_terms(studentapp)
    
    if not terms:
        return []
    
    # Get all department codes
    all_dept_codes = studentapp.get_all_dept_codes_csv()
    
    # Collect all unique course codes
    all_course_codes = set()
    
    print(f"Processing {len(terms)} terms from past 4 years...", file=sys.stderr)
    
    for i, term in enumerate(terms, 1):
        term_code = str(term['code'])
        term_name = term.get('cal_name', term_code)
        
        print(f"[{i}/{len(terms)}] Processing {term_name} ({term_code})...", file=sys.stderr)
        
        # Get all courses for this term
        args = f'subject={all_dept_codes}&term={term_code}'
        
        try:
            course_data = studentapp.get_courses(args)
            course_codes = extract_course_codes(course_data)
            all_course_codes.update(course_codes)
            print(f"  Found {len(course_codes)} courses in {term_name}", file=sys.stderr)
        except Exception as e:
            print(f"  Error processing {term_name}: {e}", file=sys.stderr)
            continue
    
    # Return sorted list
    sorted_codes = sorted(all_course_codes)
    print(f"\nTotal unique course codes: {len(sorted_codes)}", file=sys.stderr)
    
    return sorted_codes


def main():
    """
    Main entry point.
    Outputs JSON array of all course codes to stdout.
    
    Usage:
        python server/data/scraping/get_all_course_codes.py > course_codes.json
    """
    try:
        course_codes = get_all_course_codes()
        # Output compact JSON (no indentation) for smaller file size
        print(json.dumps(course_codes))
        sys.stdout.flush()
    except Exception as e:
        error_msg = {"error": str(e)}
        print(json.dumps(error_msg))
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

