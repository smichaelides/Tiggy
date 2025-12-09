#!/usr/bin/env python3
"""
Generate a JSON file mapping distribution requirements to course codes.
This creates a simple lookup: {"CD": ["AAS 232", ...], "SEL": [...], ...}
"""

import json
import os
from collections import defaultdict

def generate_distribution_mapping():
    """Generate distribution requirement to course codes mapping."""
    
    # Get paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'spring26_course_details.json')
    output_file = os.path.join(current_dir, 'distribution_to_courses.json')
    
    # Load course details
    print(f"Loading course details from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        course_details = json.load(f)
    
    # Create mapping: distribution_code -> list of course codes
    distribution_map = defaultdict(list)
    
    if 'term' not in course_details or not course_details['term']:
        print("No term data found in course details")
        return
    
    term = course_details['term'][0]
    
    # Iterate through all courses
    for subject_obj in term.get('subjects', []):
        subject_code = subject_obj.get('code', '')
        if not subject_code:
            continue
        
        for course in subject_obj.get('courses', []):
            catalog_num = course.get('catalog_number')
            if not catalog_num:
                continue
            
            course_code = f"{subject_code} {catalog_num}"
            
            # Get distribution from detail
            detail = course.get('detail', {})
            distribution = detail.get('distribution', '')
            
            if distribution:
                # Handle both list and string formats
                dist_codes = []
                if isinstance(distribution, list):
                    dist_codes = [str(d).strip().upper() for d in distribution if d]
                elif isinstance(distribution, str):
                    # Split by comma or space
                    dist_codes = [d.strip().upper() for d in distribution.replace(',', ' ').split() if d.strip()]
                
                # Normalize codes
                distribution_mapping = {
                    'STL': 'SEL',
                    'STN': 'SEN',
                    'QR': 'QCR'
                }
                
                # Add course to each distribution requirement it fulfills
                for dist_code in dist_codes:
                    normalized_code = distribution_mapping.get(dist_code, dist_code)
                    if normalized_code and normalized_code not in distribution_map[normalized_code]:
                        distribution_map[normalized_code].append(course_code)
    
    # Sort course codes for each distribution
    for dist_code in distribution_map:
        distribution_map[dist_code].sort()
    
    # Convert to regular dict and save
    result = dict(distribution_map)
    
    print(f"\nFound courses for each distribution requirement:")
    for dist_code in sorted(result.keys()):
        print(f"  {dist_code}: {len(result[dist_code])} courses")
    
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully created {output_file}")
    print(f"  Total distribution codes: {len(result)}")
    print(f"  Total course entries: {sum(len(courses) for courses in result.values())}")

if __name__ == '__main__':
    generate_distribution_mapping()

