import logging
from flask import Blueprint, session
from server.recommendations.course_recommender import (
    get_student_data,
    get_available_courses_for_prompt,
    build_recommendation_prompt,
    extract_course_details
)
from server.llm.openai_service import generate_course_recommendations

recommendations = Blueprint("recommendations", __name__, url_prefix="/recommendations")


@recommendations.route("/courses", methods=["GET"])
def get_course_recommendations():
    """
    GET /api/recommendations/courses?query=optional_user_query
    
    Returns 5 course recommendations based on student's past courses, major, and class year.
    Uses vector embeddings for semantic search when available.
    
    Query parameters:
        query: Optional user query text (e.g., "I want a statistics course")
    """
    from flask import request
    
    # Authenticate user
    user_id = session.get("userId")
    if not user_id:
        return {"error": "User not authenticated"}, 401
    
    try:
        # Get optional user query
        user_query = request.args.get("query", None)
        
        # Fetch student data
        student_data = get_student_data(user_id)
        past_courses = student_data.get("past_courses", {})
        concentration = student_data.get("concentration")
        
        # Get available courses for prompt
        available_courses = get_available_courses_for_prompt(
            past_courses=past_courses,
            concentration=concentration
        )
        
        if not available_courses:
            return {
                "error": "No courses available for recommendations",
                "message": "Unable to find courses. Please ensure your major is set in settings."
            }, 400
        
        # Build prompt with vector search enabled
        system_prompt, context_message = build_recommendation_prompt(
            student_data=student_data,
            available_courses=available_courses,
            use_vector_search=True,  # Enable vector search
            user_query=user_query
        )
        
        # Call OpenAI to get recommendations
        recommended_course_codes = generate_course_recommendations(
            system_prompt=system_prompt,
            context_message=context_message
        )
        
        # Match course codes to full course details
        course_details_list = []
        for course_code in recommended_course_codes:
            course_details = extract_course_details(course_code)
            if course_details:
                course_details_list.append(course_details)
            else:
                logging.warning(f"Could not find details for course: {course_code}")
        
        # If we couldn't find all courses, log warning
        if len(course_details_list) < 5:
            logging.warning(
                f"Only found {len(course_details_list)} out of {len(recommended_course_codes)} recommended courses"
            )
        
        # Build response
        response = {
            "courses": course_details_list
        }
        
        # Add message if no past courses
        if not past_courses:
            response["message"] = (
                "To get more personalized recommendations, please add your past courses "
                "in the Settings page. This will help us recommend courses that build on "
                "your existing knowledge."
            )
        
        return response, 200
    
    except ValueError as e:
        logging.error(f"Value error in recommendations: {e}")
        return {"error": str(e)}, 400
    except Exception as e:
        logging.error(f"Failed to generate recommendations: {e}", exc_info=True)
        return {
            "error": "Failed to generate course recommendations",
            "message": "An error occurred while generating recommendations. Please try again later."
        }, 500

