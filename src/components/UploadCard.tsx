import { useRef, useState } from "react";
const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];

interface UploadCardProps {
  onFileSelected: (file: File) => void;
}

export function UploadCard({ onFileSelected }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (file: File | undefined) => {
    if (!file) return;
    const typeOk = ALLOWED_TYPES.includes(file.type) || /\.(jpe?g|png|pdf)$/i.test(file.name);
    if (!typeOk) {
      setError("Only JPG, PNG and PDF documents are supported.");
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError("File is larger than 10 MB. Please choose a smaller file.");
      return;
    }
    setError(null);
    setSelectedFile(file);
  };

  const handleAnalyzeClick = () => {
    if (!selectedFile) {
      inputRef.current?.click();
      return;
    }
    onFileSelected(selectedFile);
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
      {/* Drop / Selection Zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload notice"
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          handleFileChange(event.dataTransfer.files?.[0]);
        }}
        className={
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-4 py-8 text-center transition-colors " +
          (dragging ? "border-primary bg-accent" : "border-border bg-secondary/50 hover:border-primary/60")
        }
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-10 w-10 text-primary"
          aria-hidden="true"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <path d="M14 2v6h6" />
          <path d="M12 18v-6" />
          <path d="m9 15 3 3 3-3" />
        </svg>

        <div>
          <p className="font-display text-lg font-semibold text-foreground">
            {selectedFile ? selectedFile.name : "Choose Notice Document"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {selectedFile
              ? `${(selectedFile.size / 1024).toFixed(1)} KB — Click to change`
              : "JPG, PNG or PDF (up to 10 MB)"}
          </p>
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            inputRef.current?.click();
          }}
          className="inline-flex items-center rounded-full border border-primary/30 bg-primary/10 px-5 py-2 font-display text-sm font-semibold text-primary transition-colors hover:bg-primary/20"
        >
          {selectedFile ? "Change File" : "Select File"}
        </button>

        <input
          ref={inputRef}
          type="file"
          id="notice-file-input"
          accept=".jpg,.jpeg,.png,.pdf"
          className="hidden"
          onChange={(event) => {
            handleFileChange(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      {/* Prominent Analyze Button */}
      <div className="mt-5 flex justify-center">
        <button
          type="button"
          id="analyze-button"
          onClick={handleAnalyzeClick}
          className="w-full sm:w-auto inline-flex items-center justify-center rounded-full bg-primary px-8 py-3 font-display text-base font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        >
          Analyze Notice
        </button>
      </div>
    </div>
  );
}
