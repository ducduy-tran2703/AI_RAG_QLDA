import * as React from "react"
import { useDropzone, DropzoneOptions } from "react-dropzone"
import { Upload, File, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "./button"

interface FileUploadZoneProps extends DropzoneOptions {
  className?: string
  label?: string
  description?: string
  files?: File[]
  onRemove?: (file: File) => void
}

export function FileUploadZone({
  className,
  label = "Kéo thả file vào đây hoặc click để chọn",
  description = "Hỗ trợ .docx, .pdf (tối đa 50MB)",
  files = [],
  onRemove,
  ...props
}: FileUploadZoneProps) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone(props)

  return (
    <div className={cn("space-y-4", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center transition-colors cursor-pointer",
          isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
        )}
      >
        <input {...getInputProps()} />
        <div className="bg-primary/10 p-4 rounded-full mb-4">
          <Upload className="h-8 w-8 text-primary" />
        </div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>

      {files.length > 0 && (
        <ul className="space-y-2">
          {files.map((file, idx) => (
            <li
              key={idx}
              className="flex items-center justify-between p-3 bg-muted/50 rounded-md border"
            >
              <div className="flex items-center gap-3">
                <File className="h-4 w-4 text-primary" />
                <div className="flex flex-col">
                  <span className="text-sm font-medium line-clamp-1">{file.name}</span>
                  <span className="text-[10px] text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
              </div>
              {onRemove && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => onRemove(file)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
