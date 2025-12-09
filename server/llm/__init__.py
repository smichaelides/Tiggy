"""
LLM Integration Module

This module handles all LLM-related functionality including:
- OpenAI API integration
- Prompt construction for chat and recommendations
- Response generation
"""

from server.llm.openai_service import (
    get_openai_client,
    generate_chat_response,
    generate_course_recommendations,
    parse_course_codes,
    normalize_course_code
)
from server.llm.chat_prompts import (
    SYSTEM_PROMPT,
    build_chat_prompt
)

__all__ = [
    'get_openai_client',
    'generate_chat_response',
    'generate_course_recommendations',
    'parse_course_codes',
    'normalize_course_code',
    'SYSTEM_PROMPT',
    'build_chat_prompt',
]

