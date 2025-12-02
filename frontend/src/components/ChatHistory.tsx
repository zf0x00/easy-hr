"use client";

import { useEffect, useState } from "react";
import { getChats } from "@/lib/api";
import { SidebarMenuItem } from "./ui/sidebar";
import { Link } from "react-router-dom";

interface Chat {
  id: string;
  title: string;
}

export default function ChatHistory() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        setIsLoading(true);
        const fetchedChats = await getChats();
        setChats(fetchedChats);
        setError(null);
      } catch (err) {
        setError(err as Error);
        console.error("Failed to fetch chats:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchChats();
  }, []);

  if (isLoading) {
    return <p>Loading chats...</p>;
  }

  if (error) {
    return <p className="text-red-500">Failed to load chats.</p>;
  }

  return (
    <div className="flex flex-col gap-1 py-2">
      {chats.length > 0 ? (
        chats.map((chat) => (
          <Link to={`/chat/${chat.id}`} key={chat.id} className="no-underline">
            <SidebarMenuItem>
              {chat.title}
            </SidebarMenuItem>
          </Link>
        ))
      ) : (
        <p className="text-sm text-muted-foreground px-4">No chats yet.</p>
      )}
    </div>
  );
}
