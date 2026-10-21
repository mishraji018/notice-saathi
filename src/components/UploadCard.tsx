import { useRef, useState } from "react";
import type { Language } from "@/lib/types";
import { t } from "@/lib/strings";

const MAX_SIZE_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"];

interface UploadCardProps {
  language: Language;
  onFileSelected: (file: File) => void;
}

export function UploadCard({ language, onFileSelected }: UploadCardProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateAndSubmit = (file: File | undefined) => {
    if (!file) return;
    const typeOk = ALLOWED_TYPES.includes(file.type) || /\.(jpe?g|png|pdf)$/i.test(file.name);
    if (!typeOk) {
      setError(t(language, "fileWrongType"));
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError(t(language, "fileTooLarge"));
      return;
    }
    setError(null);
    onFileSelected(file);
  };

  const trySample = () => {
    const sample = new File(["sample"], "sample-notice.pdf", { type: "application/pdf" });
    onFileSelected(sample);
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
      <div
        role="button"
        tabIndex={0}
        aria-label={t(language, "uploadTitle")}
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
          validateAndSubmit(event.dataTransfer.files?.[0]);
        }}
        className={
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-4 py-10 text-center transition-colors " +
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
        <p className="font-display text-lg font-semibold text-foreground">{t(language, "uploadTitle")}</p>
        <p className="max-w-xs text-sm text-muted-foreground">{t(language, "uploadHint")}</p>
        <span className="mt-2 inline-flex items-center rounded-full bg-primary px-6 py-2.5 font-display text-base font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90">
          {t(language, "uploadButton")}
        </span>
        <p className="text-xs text-muted-foreground">{t(language, "dropHint")}</p>
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf"
          className="hidden"
          onChange={(event) => {
            validateAndSubmit(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
      </div>

      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-destructive/10 px-3 py-2 text-sm font-medium text-destructive">
          {error}
        </p>
      )}

      <div className="mt-5 text-center">
        <button
          type="button"
          onClick={trySample}
          className="text-sm font-semibold text-primary hover:underline"
        >
          {t(language, "trySample")}
        </button>
      </div>
    </div>
  );
}
