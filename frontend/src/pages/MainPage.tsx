import React, { useState, useRef, useEffect } from "react";
import Header from "../components/Header";
import WelcomeScreen from "../components/WelcomeScreen";
import ChatInterface from "../components/ChatInterface";
import ChatSidebar from "../components/ChatSidebar";
import type { Message, Chat } from "../types";
import { chatAPI } from "../api/chatAPI";

const getChatTitle = (messages: Message[]) => {
  return messages.length > 0
    ? messages[0].message.substring(0, 30) +
        (messages[0].message.length > 30 ? "..." : "")
    : "New Chat";
};

function MainPage() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom whenever messages or loading state changes
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentChat?.messages]);

  // load all chats and create new chat if none exists.
  useEffect(() => {
    listChats();
  }, []);

  const listChats = async () => {
    try {
      const response = await chatAPI.listChats();
      const chats = response.chats.map((chat): Chat => {
        const userMessages = chat.userMessages.map((m: Message) => ({
          message: m.message,
          isUser: true,
          timestamp: new Date(m.timestamp),
        }));

        const modelMessages = chat.modelMessages.map((m: Message) => ({
          message: m.message,
          isUser: false,
          timestamp: new Date(m.timestamp),
        }));

        const messages = [...userMessages, ...modelMessages].sort(
          (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
        );

        return {
          _id: chat._id,
          title: getChatTitle(messages),
          userMessages: chat.userMessages,
          modelMessages: chat.modelMessages,
          messages: messages,
          createdAt: new Date(chat.createdAt),
          updatedAt: new Date(chat.updatedAt),
        };
      });

      setChats(chats);
      if (chats.length > 0) {
        setCurrentChat(chats[0]);
      }
    } catch (error) {
      console.error("Unable to list new chats:", error);
    }
  };

  const createNewChat = async () => {
    try {
      const chat = await chatAPI.createChat();

      const newChat: Chat = {
        _id: chat._id,
        title: "New Chat",
        userMessages: [],
        modelMessages: [],
        messages: [],
        createdAt: new Date(chat.createdAt),
        updatedAt: new Date(chat.updatedAt),
      };

      setChats((prev) => [...prev, newChat]);
      console.log("New chat created", newChat);
      setCurrentChat(newChat);
      setInputValue("");
    } catch (error) {
      console.error("Unable to create new chat:", error);
    }
  };

  const selectChat = async (chatId: string) => {
    // Prefer the server copy to ensure you have the freshest data; fallback to local state if API fails
    let fetchedChat;
    try {
      fetchedChat = await chatAPI.getChat(chatId); // fetch latest from backend
    } catch (err) {
      console.warn(
        "Failed to fetch chat from API, falling back to local state:",
        err
      );
      fetchedChat = chats.find((chat) => chat._id === chatId); // local fallback (may be stale)
    }

    if (!fetchedChat) return;

    const userMessages: Message[] = (fetchedChat.userMessages || []).map(
      (message: Message) => {
        const userMessage: Message = {
          message: message.message,
          isUser: true,
          timestamp: new Date(message.timestamp),
        };
        return userMessage;
      }
    );

    const modelMessages: Message[] = (fetchedChat.modelMessages || []).map(
      (message: Message) => {
        const modelMessage: Message = {
          message: message.message,
          isUser: false,
          timestamp: new Date(message.timestamp),
        };
        return modelMessage;
      }
    );

    const messages = [...userMessages, ...modelMessages].sort(
      (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
    );

    const tempChatForTitle = {
      ...(fetchedChat || {}),
      title: fetchedChat.title ?? "New Chat",
      messages,
    } as Chat;

    const currentChat: Chat = {
      _id: fetchedChat._id,
      title: getChatTitle(tempChatForTitle.messages),
      userMessages,
      modelMessages,
      messages,
      createdAt: new Date(fetchedChat.createdAt),
      updatedAt: new Date(fetchedChat.updatedAt),
    };

    setCurrentChat(currentChat);
    setInputValue("");

    setChats((prev) =>
      prev.map((c) => {
        if (c._id === chatId) {
          return currentChat;
        }
        return c;
      })
    );
  };

  const deleteChat = async (chatId: string) => {
    if (chats.length <= 1) return;

    try {
      await chatAPI.deleteChat(chatId);
    } catch (error) {
      console.error("Unable to delete chat. Ex:", chatId, error);
    }

    setChats((prev) => prev.filter((chat) => chat._id !== chatId));

    // If we're deleting the current chat, switch to new chat
    if (chatId === currentChat?._id) {
      const remainingChats = chats.filter((chat) => chat._id !== chatId);
      if (remainingChats.length > 0) {
        setCurrentChat(remainingChats[0]);
      }
    }
  };

  const updateChatMessages = (chatId: string, newMessages: Message[]) => {
    setCurrentChat((prev) => {
      if (!prev) return prev;
      const newTitle =
        prev.title === "New Chat" && newMessages.length > 0
          ? newMessages[0].message.substring(0, 30) +
            (newMessages[0].message.length > 30 ? "..." : "")
          : prev.title;
      return {
        ...prev,
        messages: newMessages,
        updatedAt: new Date(),
        title: newTitle,
      };
    });

    setChats((prev) =>
      prev.map((chat) => {
        return chat._id === chatId
          ? {
              ...chat,
              messages: newMessages,
              updatedAt: new Date(),
              title:
                chat.title === "New Chat" && newMessages.length > 0
                  ? newMessages[0].message.substring(0, 30) +
                    (newMessages[0].message.length > 30 ? "..." : "")
                  : chat.title,
            }
          : chat;
      })
    );
  };

  const handleSendMessage = async (customText?: string) => {
    const textToSend = customText || inputValue;
    if (!textToSend.trim()) return;

    if (!currentChat) {
      try {
        await createNewChat();
      } catch (ex) {
        console.error("Failed to create new chat:", ex);
        return;
      }
    }

    const userMessage: Message = {
      message: textToSend,
      isUser: true,
      timestamp: new Date(),
    };

    const chatResponse = await chatAPI.sendMessage(
      currentChat!._id,
      textToSend
    );

    updateChatMessages(currentChat!._id, [
      ...currentChat!.messages,
      userMessage,
    ]);
    setInputValue("");
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        message: chatResponse.model_message,
        isUser: false,
        timestamp: new Date(),
      };

      updateChatMessages(currentChat!._id, [
        ...currentChat!.messages,
        userMessage,
        aiMessage,
      ]);
      setIsLoading(false);
    }, 2000);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="app">
      <Header messages={currentChat?.messages ?? []} />

      <div className="main-content">
        <ChatSidebar
          chats={chats}
          currentChatId={currentChat?._id}
          onChatSelect={selectChat}
          onNewChat={createNewChat}
          onDeleteChat={deleteChat}
        />

        <main
          className={`chat-container ${
            !(currentChat && currentChat.messages.length > 0)
              ? "chat-container-with-messages"
              : ""
          }`}
        >
          {!currentChat ||
          (currentChat && currentChat.messages.length === 0) ? (
            <WelcomeScreen
              inputValue={inputValue}
              setInputValue={setInputValue}
              handleSendMessage={handleSendMessage}
              handleKeyDown={handleKeyDown}
              isLoading={isLoading}
            />
          ) : (
            <ChatInterface
              currentChat={currentChat}
              inputValue={inputValue}
              setInputValue={setInputValue}
              handleSendMessage={handleSendMessage}
              handleKeyDown={handleKeyDown}
              isLoading={isLoading}
              messagesEndRef={messagesEndRef}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default MainPage;
