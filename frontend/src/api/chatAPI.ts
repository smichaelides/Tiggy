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