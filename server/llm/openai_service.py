import os
import json
import logging
import re
from typing import List, Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Initialize OpenAI client
_openai_client: Optional[OpenAI] = None


# Get or create OpenAI client instance.
# Returns:
#     OpenAI client instance
def get_openai_client() -> OpenAI:
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    _openai_client = OpenAI(api_key=api_key)
    logging.info("OpenAI client initialized")
    return _openai_client

# Generate chat response from OpenAI API.
# Args:
#     system_prompt: System prompt defining the role and behavior
#     context_message: Context message with student data and course information
#     model: OpenAI model to use (default: "gpt-4o-mini")
#     max_retries: Maximum number of retry attempts (default: 3)
# Returns:
#     String response from the model
# Raises:
#     Exception: If OpenAI API call fails after retries
def generate_chat_response(
    system_prompt: str, 
    context_message: str, 
    model: str = "gpt-4o-mini", 
    max_retries: int = 3
) -> str:
    client = get_openai_client()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_message}
    ]

    for attempt in range(max_retries):
        try:
            logging.info(f"Calling OpenAI API for chat response (attempt {attempt + 1}/{max_retries})")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_text = response.choices[0].message.content.strip()
            logging.info(f"OpenAI chat response received: {response_text[:200]}...")
            
            return response_text
        
        except Exception as e:
            logging.error(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                continue
            else:
                raise
    
    raise Exception("Failed to generate chat response after all retries")

# Call OpenAI API to generate course recommendations.
#    Args:
#        system_prompt: System prompt defining the role and output format
#        context_message: Context message with student data and available courses
#        model: OpenAI model to use (default: "gpt-4o-mini")
#        max_retries: Maximum number of retry attempts (default: 3)   
#    Returns:
#        List of 5 course codes (e.g., ["COS 126", "ECO 100", ...])    
#    Raises:
#        ValueError: If unable to extract 5 course codes after retries
#        Exception: If OpenAI API call fails after retries
def generate_course_recommendations(
    system_prompt: str,
    context_message: str,
    model: str = "gpt-4o-mini",
    max_retries: int = 3
) -> List[str]:
    
    client = get_openai_client()
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": context_message}
    ]
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Calling OpenAI API (attempt {attempt + 1}/{max_retries})")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            response_text = response.choices[0].message.content.strip()
            logging.info(f"OpenAI response received: {response_text[:200]}...")
            
            # Parse course codes from response
            course_codes = parse_course_codes(response_text)
            
            if len(course_codes) == 5:
                logging.info(f"Successfully extracted 5 course codes: {course_codes}")
                return course_codes
            elif len(course_codes) > 5:
                logging.warning(f"Extracted {len(course_codes)} course codes, taking first 5")
                return course_codes[:5]
            else:
                logging.warning(f"Only extracted {len(course_codes)} course codes, retrying...")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise ValueError(f"Unable to extract 5 course codes. Got {len(course_codes)}: {course_codes}")
        
        except Exception as e:
            logging.error(f"OpenAI API call failed (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                continue
            else:
                raise
    
    raise ValueError("Failed to generate recommendations after all retries")


# Parse course codes from OpenAI response.
# Handles various formats: JSON array, newline-separated, comma-separated, etc.
# Args:
#     response_text: Raw response text from OpenAI
# Returns:
#     List of course codes in format "SUBJECT NUMBER"
def parse_course_codes(response_text: str) -> List[str]:
    course_codes = []
    
    # Try to parse as JSON first
    try:
        # Check if response is wrapped in JSON
        json_data = json.loads(response_text)
        if isinstance(json_data, dict):
            # Look for common keys
            if "courses" in json_data:
                course_codes = json_data["courses"]
            elif "recommendations" in json_data:
                course_codes = json_data["recommendations"]
            elif "course_codes" in json_data:
                course_codes = json_data["course_codes"]
            else:
                # Try to extract from any list value
                for value in json_data.values():
                    if isinstance(value, list):
                        course_codes = value
                        break
        elif isinstance(json_data, list):
            course_codes = json_data
        
        if course_codes:
            # Validate and normalize
            normalized = []
            for code in course_codes:
                normalized_code = normalize_course_code(code)
                if normalized_code:
                    normalized.append(normalized_code)
            return normalized[:5]
    except json.JSONDecodeError:
        pass
    
    # Try to extract course codes using regex
    # Pattern: 3 letters, space, 3 digits (e.g., "COS 126", "AAS 223")
    pattern = r'\b([A-Z]{3})\s+(\d{3})\b'
    matches = re.findall(pattern, response_text.upper())
    
    for match in matches:
        subject, number = match
        course_code = f"{subject} {number}"
        if course_code not in course_codes:
            course_codes.append(course_code)
    
    # Also try without space (e.g., "COS126")
    pattern_no_space = r'\b([A-Z]{3})(\d{3})\b'
    matches_no_space = re.findall(pattern_no_space, response_text.upper())
    
    for match in matches_no_space:
        subject, number = match
        course_code = f"{subject} {number}"
        if course_code not in course_codes:
            course_codes.append(course_code)
    
    # Normalize all codes
    normalized = []
    for code in course_codes:
        normalized_code = normalize_course_code(code)
        if normalized_code:
            normalized.append(normalized_code)
    
    return normalized[:5]


# Normalize a course code to standard format "SUBJECT NUMBER".
# Args:
#     course_code: Course code in various formats
# Returns:
#     Normalized course code or None if invalid
def normalize_course_code(course_code: str) -> Optional[str]:
    if not course_code:
        return None
    
    # Remove extra whitespace and convert to uppercase
    code = course_code.strip().upper()
    
    # Remove quotes if present
    code = code.strip('"\'')
    
    # Handle formats like "COS 126", "COS126", "COS-126"
    code = code.replace('-', ' ')
    code = re.sub(r'\s+', ' ', code)
    
    # Validate format: 3 letters, space, 3 digits
    pattern = r'^([A-Z]{3})\s+(\d{3})$'
    match = re.match(pattern, code)
    
    if match:
        subject, number = match.groups()
        return f"{subject} {number}"
    
    # Try to fix if no space
    pattern_no_space = r'^([A-Z]{3})(\d{3})$'
    match_no_space = re.match(pattern_no_space, code)
    
    if match_no_space:
        subject, number = match_no_space.groups()
        return f"{subject} {number}"
    
    logging.warning(f"Invalid course code format: {course_code}")
    return None

