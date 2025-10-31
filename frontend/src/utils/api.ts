import type { User, CreateUserRequest } from '../types';
import type { Chat } from '../types';

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
};

// Chat API functions
export const chatAPI = {
  createChat: async (): Promise<Chat> => {
    return apiRequest<Chat>('/chat/create-chat', {
      method: 'POST',
    });
  },

  // List user's chats
  listChats: async (): Promise<{ chats: Array<Chat> }> => {
    return apiRequest<{ chats: Array<Chat> }>(`/chat/list-chats`);
  },

  // Get chat with messages
  getChat: async (chatId: string): Promise<Chat> => {
    return apiRequest<Chat>(`/chat/get-chat?chatId=${chatId}`);
  },

  // Send a message
  sendMessage: async (chatId: string, message: string): Promise<{ model_message: string }> => {
    return apiRequest<{ model_message: string }>('/chat/send-message', {
      method: 'POST',
      body: JSON.stringify({
        chatId: chatId,
        message,
        timestamp: new Date().toISOString(),
      }),
    });
  },

  deleteChat: async (chatId: string): Promise<{ chatId: string }> => {
    return apiRequest<{ chatId: string }>('/chat/delete-chat', {
      method: 'DELETE',
      body: JSON.stringify({
        chatId: chatId,
      }),
    }); 
  }
};
