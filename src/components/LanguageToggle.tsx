import type { Language } from "@/lib/types";

interface LanguageToggleProps {
  language: Language;
  onChange: (language: Language) => void;
}

export function LanguageToggle({ language, onChange }: LanguageToggleProps) {
  const options: Array<{ value: Language; label: string }> = [
    { value: "en", label: "EN" },
    { value: "hi", label: "हिंदी" },
  ];

  return (
    <div
      role="group"
      aria-label="Language / भाषा"
      className="inline-flex items-center rounded-full border border-border bg-card p-1 shadow-sm"
    >
      {options.map((option) => {
        const active = option.value === language;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={
              "rounded-full px-3.5 py-1.5 text-sm font-semibold transition-colors " +
              (active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground")
            }
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
