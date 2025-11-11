import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import type { Chat } from '../types';
import tigerAvatar from "../assets/tiggy.png";


interface ChatInterfaceProps {
  currentChat: Chat;
  inputValue: string;
  setInputValue: (value: string) => void;
  handleSendMessage: (customText?: string) => void;
  handleKeyDown: (e: React.KeyboardEvent) => void;
  isLoading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
}

function ChatInterface({
  currentChat,
  inputValue,
  setInputValue,
  handleSendMessage,
  handleKeyDown,
  isLoading,
  messagesEndRef
}: ChatInterfaceProps) {

  return (
    <div className="chat-layout">
      {/* Messages */}
      <div className="messages-container">
        {currentChat.messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.isUser ? 'message-user' : 'message-ai'}`}
          >
            <div className="message-content">
              {!message.isUser && (
                <div className="avatar ai-avatar">
                  <img src={tigerAvatar} alt="Tiger AI" />
                </div>
              )}
              <div className={`message-bubble ${message.isUser ? 'user-bubble' : 'ai-bubble'}`}>
                <p className="message-text">{message.message}</p>
              </div>
            </div>
            <div className={`message-time ${message.isUser ? 'time-right' : 'time-left'}`}>
              {new Date(message.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message message-ai">
            <div className="message-content">
              <div className="avatar ai-avatar">
                <img src={tigerAvatar} alt="Tiger AI" />
              </div>
              <div className="message-bubble ai-bubble">
                <p className="message-text">Tiggy is thinking...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-container">
        <div className="input-wrapper">
          <input
            type="text"
            placeholder="Ask me anything..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="chat-input"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            <FiArrowUp />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ChatInterface; 