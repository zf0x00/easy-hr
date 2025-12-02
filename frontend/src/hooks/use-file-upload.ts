import { useState, useCallback, useRef, useEffect } from 'react';

// --- TYPES ---

export interface FileMetadata {
  id: string;
  name: string;
  size: number;
  type: string;
  url: string;
}

export interface FileWithPreview {
  id: string;
  file: File;
  preview: string;
}

// --- UTILITY FUNCTIONS ---

export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

const generateId = () => `file-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

// --- HOOK ---

interface UseFileUploadOptions {
  maxFiles?: number;
  maxSize?: number; // in bytes
  accept?: string;
  multiple?: boolean;
  initialFiles?: FileMetadata[];
  onFilesChange?: (files: FileWithPreview[]) => void;
}

export function useFileUpload({
  maxFiles = 10,
  maxSize = 50 * 1024 * 1024,
  accept = '*',
  multiple = true,
  initialFiles = [],
  onFilesChange,
}: UseFileUploadOptions) {
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [errors, setErrors] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const initialFilePreviews = initialFiles.map((f) => ({
      id: f.id,
      file: { name: f.name, size: f.size, type: f.type } as File,
      preview: f.url,
    }));
    setFiles(initialFilePreviews);
    onFilesChange?.(initialFilePreviews);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only once on mount

  const processFiles = useCallback((incomingFiles: FileList | null) => {
    if (!incomingFiles) return;

    const newErrors: string[] = [];
    let newFiles: FileWithPreview[] = [];

    Array.from(incomingFiles).forEach((file) => {
      if (files.length + newFiles.length >= maxFiles) {
        newErrors.push(`You can only upload a maximum of ${maxFiles} files.`);
        return;
      }
      if (file.size > maxSize) {
        newErrors.push(`File "${file.name}" exceeds the maximum size of ${formatBytes(maxSize)}.`);
        return;
      }
      if (accept !== '*') {
        const acceptedTypes = accept.split(',').map(t => t.trim());
        const fileType = file.type;
        const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
        if (!acceptedTypes.some(type => {
          if (type.startsWith('.')) {
            return fileExtension === type;
          }
          if (type.endsWith('/*')) {
            return fileType.startsWith(type.slice(0, -2));
          }
          return fileType === type;
        })) {
          newErrors.push(`File type for "${file.name}" is not supported. Accepted types: ${accept}`);
          return;
        }
      }

      const fileWithPreview: FileWithPreview = {
        id: generateId(),
        file,
        preview: URL.createObjectURL(file),
      };
      newFiles.push(fileWithPreview);
    });

    setErrors(newErrors);

    if (newErrors.length > 0) {
      // Clean up created object URLs for invalid files
      newFiles.forEach(f => URL.revokeObjectURL(f.preview));
      return;
    }
    
    const updatedFiles = multiple ? [...files, ...newFiles] : newFiles;
    setFiles(updatedFiles);
    onFilesChange?.(updatedFiles);

  }, [files, maxFiles, maxSize, accept, multiple, onFilesChange]);

  const removeFile = useCallback((fileId: string) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.filter((f) => f.id !== fileId);
      const fileToRemove = prevFiles.find((f) => f.id === fileId);
      if (fileToRemove && fileToRemove.preview.startsWith('blob:')) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      onFilesChange?.(updatedFiles);
      return updatedFiles;
    });
  }, [onFilesChange]);

  const clearFiles = useCallback(() => {
    files.forEach(file => {
      if (file.preview.startsWith('blob:')) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setFiles([]);
    onFilesChange?.([]);
  }, [files, onFilesChange]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  }, [processFiles]);

  const openFileDialog = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const getInputProps = useCallback(() => ({
    ref: inputRef,
    type: 'file',
    multiple,
    accept,
    onChange: handleFileChange,
  }), [multiple, accept, handleFileChange]);

  return [
    { isDragging, errors },
    {
      removeFile,
      clearFiles,
      handleDragEnter,
      handleDragLeave,
      handleDragOver,
      handleDrop,
      openFileDialog,
      getInputProps,
    },
  ] as const;
}
