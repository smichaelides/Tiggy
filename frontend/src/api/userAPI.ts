import type { User, CreateUserRequest } from '../types';

// Generic API request helper
async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `/api${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export const userAPI = {
  // Create a new user
  createUser: async (userData: CreateUserRequest): Promise<User> => {
    return apiRequest<User>('/user/create-user', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  },

  // Get user by ID
  getUser: async (): Promise<User> => {
    return apiRequest<User>(`/user/get-user`);
  },

  // Get user by email
  getUserByEmail: async (email: string): Promise<User> => {
    return apiRequest<User>(`/user/get-user-by-email?email=${email}`);
  },

  getPastCourses: async (): Promise<{"past_course": Record<string, string>}> => {
    return apiRequest<{"past_course": Record<string, string>}>('/user/get-past-courses');
  },

  // Update user concentration
  updateConcentration: async (concentration: string): Promise<{ concentration: string }> => {
    return apiRequest<{ concentration: string }>('/user/update-concentration', {
      method: 'PATCH',
      body: JSON.stringify({ concentration }),
    });
  },

  // Update user certificates
  updateCertificates: async (certificates: string[]): Promise<{ certificates: string[] }> => {
    return apiRequest<{ certificates: string[] }>('/user/update-certificates', {
      method: 'PATCH',
      body: JSON.stringify({ certificates }),
    });
  },

  // Update user info (grade, concentration)
  updateUser: async (updates: { grade?: string; concentration?: string }): Promise<User> => {
    return apiRequest<User>('/user/update-user', {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  // Update past courses
  updatePastCourses: async (pastCourses: { past_courses: Record<string, string> }): Promise<User> => {
    return apiRequest<User>('/user/update-past-courses', {
      method: 'PATCH',
      body: JSON.stringify(pastCourses)
    })
  }
};