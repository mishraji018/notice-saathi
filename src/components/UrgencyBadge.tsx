import type { Language, UrgencyLevel } from "@/lib/types";
import { t } from "@/lib/strings";

const STYLES: Record<UrgencyLevel, { badge: string; dot: string; label: "urgencyHigh" | "urgencyMedium" | "urgencyLow" }> = {
  high: {
    badge: "border-destructive/25 bg-destructive/10 text-destructive",
    dot: "bg-destructive",
    label: "urgencyHigh",
  },
  medium: {
    badge: "border-warning/30 bg-warning/10 text-warning",
    dot: "bg-warning",
    label: "urgencyMedium",
  },
  low: {
    badge: "border-primary/25 bg-primary/10 text-primary",
    dot: "bg-primary",
    label: "urgencyLow",
  },
};

export function UrgencyBadge({ level, language }: { level: UrgencyLevel; language: Language }) {
  const style = STYLES[level];
  return (
    <span
      className={
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold whitespace-nowrap " +
        style.badge
      }
    >
      <span className={"h-2 w-2 rounded-full " + style.dot} aria-hidden="true" />
      {t(language, style.label)}
    </span>
  );
}
