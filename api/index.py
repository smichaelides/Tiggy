"""
Vercel serverless function entry point for Flask application.
This file handles all API routes using a catch-all pattern.

Vercel automatically routes /api/* requests to functions in the api/ directory.
"""
import sys
import os

# Add the parent directory to the Python path so we can import server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import create_app

# Create Flask app instance (created once, reused across invocations)
app = create_app()

# Vercel serverless function handler
def handler(request):
    """
    Handler function for Vercel serverless functions.
    Converts Vercel Request to Flask WSGI and returns Vercel Response format.
    
    IMPORTANT: Vercel routes /api/* to this function, and Flask routes are
    registered with /api prefix. We need to strip /api from PATH_INFO to
    avoid double prefix (e.g., /api/api/auth/login -> /api/auth/login).
    """
    from io import BytesIO
    
    # Extract request details from Vercel Request object
    method = request.method
    path = request.path  # This will be like "/api/auth/login"
    headers = dict(request.headers) if hasattr(request, 'headers') else {}
    body = request.body if hasattr(request, 'body') else b''
    query_string = request.query_string if hasattr(request, 'query_string') else ''
    
    # CRITICAL FIX: Strip /api prefix from path since Flask routes already have /api prefix
    # Vercel routes /api/* to this function, so path includes /api
    # But Flask blueprints are registered with url_prefix="/api"
    # So we need to remove /api from PATH_INFO to avoid /api/api/...
    if path.startswith('/api'):
        path = path[4:]  # Remove '/api' (4 characters)
    if not path:
        path = '/'  # Ensure we have at least '/'
    
    # Build WSGI environ dictionary
    environ = {
        'REQUEST_METHOD': method,
        'SCRIPT_NAME': '/api',  # This tells Flask the base path is /api
        'PATH_INFO': path,       # Path without /api prefix
        'QUERY_STRING': query_string,
        'CONTENT_TYPE': headers.get('Content-Type', ''),
        'CONTENT_LENGTH': str(len(body)),
        'SERVER_NAME': headers.get('Host', 'localhost'),
        'SERVER_PORT': headers.get('X-Forwarded-Port', '80'),
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': headers.get('X-Forwarded-Proto', 'https'),
        'wsgi.input': BytesIO(body),
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers to environ (WSGI format)
    for key, value in headers.items():
        key_upper = key.upper().replace('-', '_')
        if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key_upper = f'HTTP_{key_upper}'
        environ[key_upper] = value
    
    # Call Flask app with WSGI interface
    response_data = {'status': None, 'headers': []}
    
    def start_response(status, response_headers):
        response_data['status'] = status
        response_data['headers'] = response_headers
    
    # Execute Flask app
    result = app(environ, start_response)
    
    # Collect response body
    body_parts = []
    try:
        for part in result:
            if part:
                body_parts.append(part)
    finally:
        if hasattr(result, 'close'):
            result.close()
    
    response_body = b''.join(body_parts)
    
    # Parse status code from status string (e.g., "200 OK")
    status_code = int(response_data['status'].split()[0])
    
    # Convert headers to dict
    response_headers = dict(response_data['headers'])
    
    # Return Vercel Response format
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body)
    }
