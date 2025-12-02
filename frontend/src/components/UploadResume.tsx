"use client";

import { useState, useCallback } from "react";
import { api } from "../lib/api";
import {
  formatBytes,
  useFileUpload,
  type FileMetadata,
  type FileWithPreview,
} from "@/hooks/use-file-upload";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  FileTextIcon,
  ImageIcon,
  Loader2,
  RefreshCwIcon,
  TriangleAlert,
  Upload,
  XIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Simplified FileUploadItem for our purpose
interface FileUploadItem extends FileWithPreview {
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
}

// Props for the UploadResume component
interface UploadResumeProps {
  className?: string;
  onSuccess?: () => void;
  onError?: (error: Error) => void;
}

export default function UploadResume({
  className,
  onSuccess,
  onError,
}: UploadResumeProps) {
  const [uploadFiles, setUploadFiles] = useState<FileUploadItem[]>([]);

  const handleUpload = useCallback(
    async (filesToUpload: { id: string; file: File }[]) => {
      if (!filesToUpload || filesToUpload.length === 0) return;

      const fileIdsToUpload = filesToUpload.map((f) => f.id);

      setUploadFiles((prev) =>
        prev.map((item) =>
          fileIdsToUpload.includes(item.id)
            ? { ...item, status: "uploading", error: undefined }
            : item,
        ),
      );

      const form = new FormData();
      filesToUpload.forEach(({ file }) => {
        form.append("files", file);
      });

      try {
        const response = await api.post("/upload", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        console.log(response, "response 🎉");

        const results: {
          status: string;
          filename: string;
          detail?: string;
        }[] = response.data.results;

        setUploadFiles((prev) =>
          prev.map((item) => {
            const result = results.find((r) => r.filename === item.file.name);
            if (result) {
              return {
                ...item,
                status: result.status === "ok" ? "completed" : "error",
                error: result.detail,
              };
            }
            return item;
          }),
        );

        if (results.some((r) => r.status === "ok")) {
          onSuccess?.();
        }
        if (results.every((r) => r.status === "error")) {
          onError?.(new Error("All uploads failed."));
        } else if (results.some((r) => r.status === "error")) {
          const failedFiles = results
            .filter((r) => r.status === "error")
            .map((r) => r.filename)
            .join(", ");
          onError?.(new Error(`Some files failed to upload: ${failedFiles}`));
        }
      } catch (err) {
        const error = err instanceof Error ? err : new Error("Upload failed");
        setUploadFiles((prev) =>
          prev.map((item) =>
            fileIdsToUpload.includes(item.id)
              ? { ...item, status: "error", error: error.message }
              : item,
          ),
        );
        onError?.(error);
      }
    },
    [onSuccess, onError],
  );

  const [
    { isDragging, errors },
    {
      removeFile,
      handleDragEnter,
      handleDragLeave,
      handleDragOver,
      handleDrop,
      openFileDialog,
      getInputProps,
    },
  ] = useFileUpload({
    maxFiles: 3,
    maxSize: 500 * 1024, // 5MB
    accept: "application/pdf",
    multiple: true,
    onFilesChange: (newFiles) => {
      if (newFiles.length > 0) {
        const newUploadItems: FileUploadItem[] = newFiles
          .map((newFile) => {
            if (newFile.file instanceof File) {
              return {
                ...newFile,
                status: "pending",
              };
            }
            return null;
          })
          .filter((item): item is FileUploadItem => item !== null);

        setUploadFiles((prev) => [...prev, ...newUploadItems]);

        const filesToUpload = newUploadItems.map((item) => ({
          id: item.id,
          file: item.file as File,
        }));
        handleUpload(filesToUpload);
      }
    },
  });

  const removeUploadFile = (id: string) => {
    removeFile(id);
    setUploadFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const retryUpload = (uploadFile: FileUploadItem) => {
    if (uploadFile && uploadFile.file instanceof File) {
      handleUpload([{ id: uploadFile.id, file: uploadFile.file as File }]);
    }
  };

  const getFileIcon = (file: File | FileMetadata) => {
    if (file.type.startsWith("image/")) return <ImageIcon className="size-6" />;
    if (file.type.includes("pdf")) return <FileTextIcon className="size-6" />;
    return <FileTextIcon className="size-6" />;
  };

  return (
    <div className={cn("w-full space-y-4", className)}>
      {/* Upload Area - only show if no file is selected */}
      {uploadFiles.length === 0 && (
        <div
          className={cn(
            "relative rounded-lg border border-dashed p-6 text-center transition-colors",
            isDragging
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-muted-foreground/50",
          )}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            {...getInputProps()}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />

          <div className="flex flex-col items-center gap-4">
            <div
              className={cn(
                "flex h-12 w-12 items-center justify-center rounded-full bg-muted transition-colors",
                isDragging
                  ? "border-primary bg-primary/10"
                  : "border-muted-foreground/25",
              )}
            >
              <Upload className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium">
                Drop PDFs here or{" "}
                <Button variant="outline" onClick={openFileDialog}>
                  browse files
                </Button>
              </p>
              <p className="text-xs text-muted-foreground">
                PDF only, up to 500KB, Max 3 Files
              </p>
            </div>
          </div>
        </div>
      )}

      {/* File Display */}
      {uploadFiles.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Selected Resumes</h3>
          <div className="grid grid-cols-1 gap-4">
            {uploadFiles.map((uploadFile) => (
              <div key={uploadFile.id} className="relative group">
                <Button
                  onClick={() => removeUploadFile(uploadFile.id)}
                  variant="ghost"
                  size="icon"
                  className="absolute -end-2 -top-2 z-10 h-6 w-6 rounded-full opacity-0 transition-opacity group-hover:opacity-100"
                >
                  <XIcon className="size-3" />
                </Button>
                <div className="relative overflow-hidden rounded-lg border bg-card transition-colors">
                  <div className="relative flex items-center space-x-4 p-3">
                    <div className="flex-shrink-0 text-muted-foreground/80">
                      {getFileIcon(uploadFile.file)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-sm font-medium">
                        {uploadFile.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatBytes(uploadFile.file.size)}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      {uploadFile.status === "uploading" && (
                        <Loader2 className="size-5 animate-spin text-muted-foreground" />
                      )}
                      {uploadFile.status === "completed" && (
                        <div className="text-xs font-medium text-green-600">
                          Uploaded
                        </div>
                      )}
                      {uploadFile.status === "error" && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              onClick={() => retryUpload(uploadFile)}
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:bg-destructive/10 hover:text-destructive"
                            >
                              <RefreshCwIcon className="size-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              {uploadFile.error ||
                                "Upload failed. Click to retry."}
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Messages from hook */}
      {errors.length > 0 && (
        <Alert variant="destructive" className="mt-5">
          <TriangleAlert />
          <AlertTitle>File Error</AlertTitle>
          <AlertDescription>
            {errors.map((error, index) => (
              <p key={index}>{error}</p>
            ))}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
