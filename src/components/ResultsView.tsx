import { useState } from "react";
import type { Language, NoticeAnalysis } from "@/lib/types";
import { t } from "@/lib/strings";
import { downloadReminder, speakText, stopSpeaking } from "@/lib/api";
import { UrgencyBadge } from "@/components/UrgencyBadge";

interface ResultsViewProps {
  analysis: NoticeAnalysis;
  language: Language;
  onStartOver: () => void;
}

function Icon({ path, className }: { path: string; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className ?? "h-4 w-4"}
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}

const ICONS = {
  speaker: "M11 5 6 9H2v6h4l5 4V5zm6 3a4 4 0 0 1 0 8m2.5-11a8 8 0 0 1 0 14",
  calendar: "M8 2v4m8-4v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z",
  phone: "M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.4 2.1L8.1 10a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.6 1.9z",
};

export function ResultsView({ analysis, language, onStartOver }: ResultsViewProps) {
  const [visibleSource, setVisibleSource] = useState<number | null>(null);
  const [speaking, setSpeaking] = useState(false);

  const facts: Array<{ label: string; value: string }> = [];
  if (analysis.authority) facts.push({ label: t(language, "authority"), value: analysis.authority });
  if (analysis.deadline) facts.push({ label: t(language, "deadline"), value: analysis.deadline });
  if (analysis.amount) facts.push({ label: t(language, "amount"), value: analysis.amount });

  const scammy = analysis.scam_likelihood === "high" || analysis.scam_likelihood === "medium";

  const handleListen = async () => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    const text = analysis.explanation_points.map((point) => point.text).join(" ");
    setSpeaking(true);
    await speakText(text, language);
    // The built-in speech cannot report completion reliably; reset after a while.
    window.setTimeout(() => setSpeaking(false), Math.max(8, Math.min(90, text.length / 12)) * 1000);
  };

  return (
    <div className="space-y-4">
      {/* Header card */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {t(language, "noticeType")}
            </p>
            <h2 className="mt-1 font-display text-2xl font-bold leading-snug text-foreground">
              {analysis.notice_type}
            </h2>
          </div>
          <UrgencyBadge level={analysis.urgency_level} language={language} />
        </div>
        {analysis.is_demo && (
          <p className="mt-3 inline-flex rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
            {t(language, "demoNotice")}
          </p>
        )}
      </div>

      {/* Scam warning */}
      {scammy && (
        <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-5" role="alert">
          <h3 className="flex items-center gap-2 font-display text-base font-bold text-destructive">
            <span aria-hidden="true">⚠</span> {t(language, "scamWarningTitle")}
          </h3>
          {analysis.scam_reasons.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-destructive">
              {analysis.scam_reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Key facts */}
      {facts.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-3">
          {facts.map((fact) => (
            <div key={fact.label} className="rounded-2xl border border-border bg-card p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{fact.label}</p>
              <p className="mt-1 text-sm font-semibold text-foreground">{fact.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* What this means */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h3 className="font-display text-lg font-bold text-foreground">{t(language, "whatItMeans")}</h3>
        <ul className="mt-3 space-y-3">
          {analysis.explanation_points.map((point, index) => {
            const open = visibleSource === index;
            return (
              <li key={index} className="flex gap-3">
                <span
                  className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-primary/10 font-display text-xs font-bold text-primary"
                  aria-hidden="true"
                >
                  {index + 1}
                </span>
                <div className="min-w-0">
                  <p className="text-sm leading-relaxed text-foreground">{point.text}</p>
                  <button
                    type="button"
                    onClick={() => setVisibleSource(open ? null : index)}
                    className="mt-1 text-xs font-semibold text-primary hover:underline"
                  >
                    {open ? t(language, "hideSource") : t(language, "viewSource")}
                  </button>
                  {open && (
                    <blockquote className="mt-1.5 border-l-2 border-primary/40 pl-3 text-sm italic text-muted-foreground">
                      “{point.source_sentence}”
                    </blockquote>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
        <button
          type="button"
          onClick={handleListen}
          className="mt-5 inline-flex items-center gap-2 rounded-full border border-primary/40 bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition-colors hover:bg-primary/20"
        >
          <Icon path={ICONS.speaker} />
          {speaking ? t(language, "stopListening") : t(language, "listen")}
        </button>
      </div>

      {/* What you need to do */}
      <div className="rounded-2xl border border-primary/30 bg-primary/5 p-6 shadow-sm">
        <h3 className="font-display text-lg font-bold text-foreground">{t(language, "whatToDo")}</h3>
        <p className="mt-2 text-sm leading-relaxed text-foreground">{analysis.action_required}</p>
        {analysis.deadline && (
          <button
            type="button"
            onClick={() => downloadReminder(analysis.notice_type, analysis.deadline as string, language)}
            className="mt-4 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 font-display text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
          >
            <Icon path={ICONS.calendar} />
            {t(language, "addReminder")}
          </button>
        )}
      </div>

      {/* Helpline */}
      {analysis.helpline && (
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            {t(language, "helpline")}
          </p>
          <a
            href={`tel:${analysis.helpline.number.replace(/[^+\d]/g, "")}`}
            className="mt-1 inline-flex items-center gap-2 font-display text-base font-bold text-primary hover:underline"
          >
            <Icon path={ICONS.phone} />
            {analysis.helpline.number}
            <span className="text-sm font-medium text-muted-foreground">({analysis.helpline.name})</span>
          </a>
        </div>
      )}

      {/* Disclaimer */}
      {analysis.is_high_risk && (
        <p className="rounded-2xl border border-border bg-secondary p-4 text-sm leading-relaxed text-muted-foreground">
          {t(language, "notLegalAdvice")}
        </p>
      )}

      <div className="text-center">
        <button
          type="button"
          onClick={onStartOver}
          className="text-sm font-semibold text-primary hover:underline"
        >
          {t(language, "startOver")}
        </button>
      </div>
    </div>
  );
}
