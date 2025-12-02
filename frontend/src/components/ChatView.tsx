"use client";
import { getChat, addMessages } from "@/lib/api";
import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import ResultCard, { parseLLMResponse } from "./ResultCard";
import PromptInputComponent from "../components/PromptInput";

export default function ChatView() {
  const { chatId } = useParams<{ chatId: string }>();
  const [chat, setChat] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (!chatId) return;

    const fetchChat = async () => {
      try {
        setIsLoading(true);
        const fetchedChat = await getChat(chatId);
        setChat(fetchedChat);
        setError(null);
      } catch (err) {
        setError(err as Error);
        console.error("Failed to fetch chat:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchChat();
  }, [chatId]);

  useEffect(() => {
    scrollToBottom();
  }, [chat?.messages]);

  const handleContinueChat = async (messages: any[]) => {
    if (!chatId) return;

    // Optimistically update UI with new messages
    setChat((prevChat: any) => ({
      ...prevChat,
      messages: [...prevChat.messages, ...messages],
    }));

    try {
      // Persist messages to the backend
      await addMessages(chatId, messages);
    } catch (err) {
      console.error("Failed to save messages:", err);
      // Handle error, e.g., show a toast notification
      // You could also revert the optimistic update here if needed
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        Loading chat...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        Failed to load chat.
      </div>
    );
  }

  if (!chat) {
    return null;
  }

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 w-full max-w-6xl mx-auto">
        {chat.messages.map((message: any, index: number) => {
          if (message.role === "user") {
            return (
              <div key={index} className="flex justify-end">
                <div className="px-4 py-2 rounded-lg bg-blue-500 text-white max-w-2xl">
                  {message.content}
                </div>
              </div>
            );
          } else {
            // Assistant message
            let candidates;
            try {
              const parsed = JSON.parse(message.content);
              if (Array.isArray(parsed)) {
                candidates = parsed;
              }
            } catch (e) {
              // Not a JSON array
            }

            if (candidates) {
              return (
                <div
                  key={index}
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full"
                >
                  {candidates.map((candidate, idx) => (
                    <ResultCard
                      key={candidate.id || idx}
                      candidate={candidate}
                      index={idx}
                    />
                  ))}
                </div>
              );
            } else if (message.content.includes("**")) {
              // Fallback for old, LLM-formatted messages
              const oldCandidates = parseLLMResponse(message.content);
              return (
                <div
                  key={index}
                  className="flex flex-col items-start w-full space-y-4"
                >
                  {oldCandidates.map((candidate, idx) => (
                    <ResultCard key={idx} candidate={candidate} index={idx} />
                  ))}
                </div>
              );
            } else {
              // Fallback for regular text messages
              return (
                <div key={index} className="flex justify-start">
                  <div className="px-4 py-2 rounded-lg bg-gray-200 text-black max-w-2xl">
                    {message.content}
                  </div>
                </div>
              );
            }
          }
        })}
        <div ref={messagesEndRef} />
      </div>
      <div className="w-full max-w-2xl mx-auto pb-4 px-4">
        <PromptInputComponent
          onNewChat={handleContinueChat}
          showResults={false}
        />
      </div>
    </div>
  );
}
