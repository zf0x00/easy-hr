"use client"

import { useState, useCallback } from "react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
} from "@/components/ui/sidebar";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Plus, UploadCloudIcon } from "lucide-react";
import UploadResume from "./UploadResume";
import ChatHistory from "./ChatHistory";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner"

export function AppSidebar() {
  const navigate = useNavigate();
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // Handler for successful upload completion
  const handleUploadSuccess = useCallback(() => {
    setIsDialogOpen(false);
    // You could add a toast notification here for user feedback
    console.log('Resume uploaded successfully');
    toast.success("Resume uploaded successfully")
  }, []);

  // Handler for upload errors
  const handleUploadError = useCallback((error: Error) => {
    console.error('Upload failed:', error);
    // You could show a toast notification here for error feedback
  }, []);

  return (
    <Sidebar>
      <SidebarHeader>
        <h2 className="text-xl font-semibold text-center">Auto HR</h2>
      </SidebarHeader>
      <SidebarContent>
         <SidebarGroup>
          <Button variant="outline" onClick={() => navigate('/')}><Plus /> New Chat</Button>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Chats</SidebarGroupLabel>
          <SidebarGroupContent className="px-2">
            <ChatHistory />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button
              variant="default"
              className="w-full"
              aria-label="Upload resume"
            >
              <UploadCloudIcon className="mr-2 h-4 w-4" aria-hidden="true" />
              Upload Resume
            </Button>
          </DialogTrigger>
          <DialogContent
            className="sm:max-w-[600px]"
            onCloseAutoFocus={(e) => e.preventDefault()} // Prevent focus restoration
          >
            <DialogHeader>
              <DialogTitle>Upload Resume</DialogTitle>
            </DialogHeader>
            <div className="mt-4">
              <UploadResume
                onSuccess={handleUploadSuccess}
                onError={handleUploadError}
              />
            </div>
          </DialogContent>
        </Dialog>
      </SidebarFooter>
    </Sidebar>
  );
}

