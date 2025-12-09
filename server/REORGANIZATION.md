# Server Directory Reorganization

## New Structure

The server directory has been reorganized into logical modules:

```
server/
├── llm/                    # LLM integration and prompts
│   ├── __init__.py
│   ├── chat_prompts.py     # Chat prompt construction (from services/chat_response.py)
│   └── openai_service.py   # OpenAI API integration
│
├── search/                 # Vector search and embeddings
│   ├── __init__.py
│   ├── embeddings.py       # Embedding utilities (from services/embeddings_utils.py)
│   └── generate_embeddings.py  # Script to generate embeddings
│
├── recommendations/        # Course recommendation logic
│   ├── __init__.py
│   └── course_recommender.py  # Main recommendation logic
│
├── core/                   # Core utilities
│   ├── __init__.py
│   ├── database.py        # Database connection management
│   └── utils.py           # General utilities
│
├── api/                    # API routes and models (unchanged)
├── data/                   # Data files and scripts (unchanged)
└── services/               # Legacy folder (can be removed after verification)
```

## Import Changes

All imports have been updated to use the new structure:

### Old Imports → New Imports

- `from server.services.chat_response import ...` → `from server.llm.chat_prompts import ...`
- `from server.services.openai_service import ...` → `from server.llm.openai_service import ...`
- `from server.services.embeddings_utils import ...` → `from server.search.embeddings import ...`
- `from server.services.course_recommender import ...` → `from server.recommendations.course_recommender import ...`
- `from server.database import ...` → `from server.core.database import ...`
- `from server.utils import ...` → `from server.core.utils import ...`

## Module Responsibilities

### `llm/` - LLM Integration
- **chat_prompts.py**: Builds chat prompts for conversational queries
- **openai_service.py**: Handles all OpenAI API calls (chat, recommendations, parsing)

### `search/` - Vector Search
- **embeddings.py**: Embedding generation, cosine similarity, vector operations
- **generate_embeddings.py**: Script to pre-compute and store course embeddings

### `recommendations/` - Recommendations
- **course_recommender.py**: 
  - Course data loading and caching
  - Distribution requirement lookups
  - Vector search integration
  - Filtering and reranking
  - Recommendation prompt building

### `core/` - Core Utilities
- **database.py**: MongoDB connection management (Flask and standalone)
- **utils.py**: General utility functions

## Migration Status

✅ All files moved to new locations
✅ All imports updated in:
   - API routes (chat.py, recommendations.py, user.py, auth.py)
   - Moved modules themselves
   - generate_embeddings.py
✅ __init__.py files created for clean imports
✅ Backward compatibility maintained (old files still exist as copies)

## Next Steps

1. **Test the application** to ensure all imports work correctly
2. **Remove old files** from `services/` once verified:
   - `services/chat_response.py` (now in `llm/chat_prompts.py`)
   - `services/openai_service.py` (now in `llm/openai_service.py`)
   - `services/embeddings_utils.py` (now in `search/embeddings.py`)
   - `services/course_recommender.py` (now in `recommendations/course_recommender.py`)
3. **Remove old root files** once verified:
   - `generate_embeddings.py` (now in `search/generate_embeddings.py`)
   - `database.py` (now in `core/database.py`)
   - `utils.py` (now in `core/utils.py`)

## Benefits

1. **Clearer organization**: Related functionality grouped together
2. **Easier navigation**: Know where to find things
3. **Better maintainability**: Changes to one area don't affect others
4. **Cleaner imports**: More descriptive import paths
5. **Scalability**: Easy to add new modules (e.g., `analytics/`, `cache/`)

