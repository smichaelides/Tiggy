// Generic API request helper
// Uses environment variable for API base URL, falls back to relative path for local dev
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  // If API_BASE_URL is set, use it (for production with separate backend)
  // Otherwise, use relative path (for local dev with Vite proxy)
  const baseUrl = API_BASE_URL || '';
  const url = `${baseUrl}/api${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // Include cookies for session management
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};
