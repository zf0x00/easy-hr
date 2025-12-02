import { AppSidebar } from "./components/app-sidebar";
import ChatView from "./components/ChatView";
import PromptInputComponent from "./components/PromptInput";
import { Routes, Route, useNavigate } from "react-router-dom";
import { createChat } from "./lib/api";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Toaster } from "@/components/ui/sonner"

export default function App() {
  const navigate = useNavigate();

  const handleNewChat = async (messages: any[]) => {
    const newChat = await createChat(messages);
    navigate(`/chat/${newChat.id}`);
  };

  return (
    <div className="flex h-screen w-screen">
      <SidebarProvider>
        <AppSidebar />
        <main className="flex-1 flex flex-col items-center justify-center p-4">
          <Routes>
            <Route
              path="/"
              element={
                <div className="flex flex-col items-center justify-end pb-8 h-full w-full">
                  <div className="flex-grow" />
                  <div className="w-full max-w-2xl">
                    <PromptInputComponent onNewChat={handleNewChat} />
                  </div>
                </div>
              }
            />
            <Route path="/chat/:chatId" element={<ChatView />} />
          </Routes>
        </main>
        <Toaster />
      </SidebarProvider>
    </div>
  );
}
