import type { Chat } from '../types';
import { apiRequest } from '../utils/api';

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