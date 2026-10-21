import type { Language } from "@/lib/types";
import { t } from "@/lib/strings";

export function LoadingState({ language }: { language: Language }) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-border bg-card px-6 py-14 text-center shadow-sm">
      <div
        className="h-10 w-10 animate-spin rounded-full border-4 border-primary/25 border-t-primary"
        role="status"
        aria-label={t(language, "analyzing")}
      />
      <p className="font-display text-lg font-semibold text-foreground">{t(language, "analyzing")}</p>
    </div>
  );
}
