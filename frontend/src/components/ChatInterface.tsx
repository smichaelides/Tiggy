import React from 'react';
import { FiArrowUp } from 'react-icons/fi';
import type { Chat } from '../types';
import tigerAvatar from "../assets/tiggy.png";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";


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
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  h1: ({node, ...props}) => <h1 className="markdown-h1" {...props} />,
                  h2: ({node, ...props}) => <h2 className="markdown-h2" {...props} />,
                  h3: ({node, ...props}) => <h3 className="markdown-h3" {...props} />,
                  p: ({node, ...props}) => <p className="markdown-p" {...props} />,
                  strong: ({node, ...props}) => <strong className="markdown-strong" {...props} />,
                  em: ({node, ...props}) => <em className="markdown-em" {...props} />,
                  ul: ({node, ...props}) => <ul className="markdown-ul" {...props} />,
                  ol: ({node, ...props}) => <ol className="markdown-ol" {...props} />,
                  li: ({node, ...props}) => <li className="markdown-li" {...props} />,
                  code: ({node, inline, ...props}: any) => 
                    inline ? (
                      <code className="markdown-code-inline" {...props} />
                    ) : (
                      <code className="markdown-code-block" {...props} />
                    ),
                  pre: ({node, ...props}) => <pre className="markdown-pre" {...props} />,
                  blockquote: ({node, ...props}) => <blockquote className="markdown-blockquote" {...props} />,
                  a: ({node, ...props}) => <a className="markdown-a" {...props} />,
                }}
              >
                {message.message}
              </ReactMarkdown>
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