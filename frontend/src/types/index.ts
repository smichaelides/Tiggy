export interface Message {
  message: string;
  isUser: boolean;
  timestamp: Date;
}

export interface Chat {
  _id: string;
  title: string;
  messages: Message[];
  userMessages: Message[];
  modelMessages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

export interface OnboardingInfo {
  name?: string;
  email?: string;
  grade?: string;
  concentration?: string;
  favoriteClasses?: string[];
}

export interface User {
  _id: string;
  name: string;
  email: string;
  grad_year: number;
  concentration?: string;
  certificates: string[];
}

export interface CreateUserRequest {
  name: string;
  email: string;
  grad_year: number;
  concentration?: string;
  certificates?: string[];
} 