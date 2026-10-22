import type { NoticeAnalysis } from "@/lib/types";
import { UrgencyBadge } from "@/components/UrgencyBadge";

interface ResultsViewProps {
  analysis: NoticeAnalysis;
  onStartOver: () => void;
}

export function ResultsView({ analysis, onStartOver }: ResultsViewProps) {
  const category = analysis.document_category || "government_notice";

  // -------------------------------------------------------------
  // Case 1: "not_government"
  // -------------------------------------------------------------
  if (category === "not_government") {
    const docType = analysis.detected_type || "non-government document";
    return (
      <div className="space-y-6">
        {/* Big clear heading banner */}
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-8 text-center shadow-sm">
          <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-full bg-secondary text-2xl" aria-hidden="true">
            📄
          </div>
          <h2 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            This does not look like a government document
          </h2>
          <p className="mt-2 text-base text-muted-foreground">
            It looks like a <span className="font-semibold text-foreground">{docType.toLowerCase()}</span>.
          </p>
        </div>

        {/* Footer & Upload Another Notice */}
        <div className="pt-2 text-center space-y-3">
          <p className="text-xs text-muted-foreground">
            This explanation is for informational purposes only and is not legal advice.
          </p>
          <div>
            <button
              type="button"
              id="upload-another-button"
              onClick={onStartOver}
              className="inline-flex items-center justify-center rounded-full bg-primary px-7 py-3 font-display text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              Upload another notice
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Case 2: "government_document_other"
  // -------------------------------------------------------------
  if (category === "government_document_other") {
    return (
      <div className="space-y-5">
        {/* Large neutral banner */}
        <div className="rounded-2xl border border-border bg-secondary/80 p-5 text-center shadow-sm">
          <p className="font-display text-base sm:text-lg font-bold text-foreground">
            This is a government document, but not a notice. No action is required.
          </p>
        </div>

        {/* Document Title Card */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Document
          </p>
          <h2 className="mt-1 font-display text-2xl font-bold leading-snug text-foreground">
            {analysis.notice_type || "Government Document"}
          </h2>
          {analysis.authority && (
            <p className="mt-1 text-sm text-muted-foreground font-medium">
              Issued by: <span className="text-foreground">{analysis.authority}</span>
            </p>
          )}
        </div>

        {/* What this document says card */}
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
          <h3 className="font-display text-lg font-bold text-foreground">
            What this document says
          </h3>
          {analysis.explanation_points && analysis.explanation_points.length > 0 ? (
            <ul className="mt-3 space-y-2.5">
              {analysis.explanation_points.map((point, index) => (
                <li key={index} className="flex items-start gap-3">
                  <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                  <p className="text-sm leading-relaxed text-foreground">{point.text}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">
              This document is an official government record or acknowledgement.
            </p>
          )}
        </div>

        {/* Keep safe line */}
        <div className="rounded-2xl border border-border bg-card p-5 text-sm text-foreground shadow-sm flex items-center gap-3">
          <span className="text-xl" aria-hidden="true">📁</span>
          <p className="leading-relaxed">
            <span className="font-semibold">Keep it safe:</span> Please store this document for your records. No immediate compliance action is required.
          </p>
        </div>

        {/* Footer & Upload Another Notice */}
        <div className="pt-2 text-center space-y-3">
          <p className="text-xs text-muted-foreground">
            This explanation is for informational purposes only and is not legal advice.
          </p>
          <div>
            <button
              type="button"
              id="upload-another-button"
              onClick={onStartOver}
              className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-2.5 font-display text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              Upload another notice
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Case 3: "government_notice" (Full 5 cards with urgency badge)
  // -------------------------------------------------------------
  const rawActions = analysis.action_required || "No immediate action specified.";
  const actionItems = rawActions
    .split(/\n+|\d+\.\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  return (
    <div className="space-y-5">
      {/* 1. Notice Type Card with Urgency Badge */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Notice Type
            </p>
            <h2 className="mt-1 font-display text-2xl font-bold leading-snug text-foreground">
              {analysis.notice_type || "Government Notice"}
            </h2>
            {analysis.authority && (
              <p className="mt-1 text-sm text-muted-foreground font-medium">
                Issued by: <span className="text-foreground">{analysis.authority}</span>
              </p>
            )}
          </div>
          {analysis.urgency_level && (
            <UrgencyBadge level={analysis.urgency_level} language="en" />
          )}
        </div>
      </div>

      {/* 2. What this notice means (Kya kehta hai) */}
      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <h3 className="font-display text-lg font-bold text-foreground">
          What this notice says
        </h3>
        {analysis.explanation_points && analysis.explanation_points.length > 0 ? (
          <ul className="mt-3 space-y-2.5">
            {analysis.explanation_points.map((point, index) => (
              <li key={index} className="flex items-start gap-3">
                <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" aria-hidden="true" />
                <p className="text-sm leading-relaxed text-foreground">{point.text}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            No specific explanation points available for this notice.
          </p>
        )}
      </div>

      {/* 3 & 4. Deadline and Amount Cards */}
      <div className={`grid gap-4 ${analysis.amount ? "sm:grid-cols-2" : "grid-cols-1"}`}>
        {/* Deadline Card */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Deadline
          </p>
          <p className="mt-1.5 font-display text-lg font-bold text-foreground">
            {analysis.deadline || "No specific deadline mentioned"}
          </p>
        </div>

        {/* Amount Card (Only shown if amount exists) */}
        {analysis.amount && (
          <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Amount Involved
            </p>
            <p className="mt-1.5 font-display text-lg font-bold text-foreground">
              {analysis.amount}
            </p>
          </div>
        )}
      </div>

      {/* 5. What you need to do (Kya karna hai) */}
      <div className="rounded-2xl border border-primary/25 bg-primary/5 p-6 shadow-sm">
        <h3 className="font-display text-lg font-bold text-foreground">
          What you need to do
        </h3>
        {actionItems.length > 1 ? (
          <ol className="mt-3 space-y-2">
            {actionItems.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-sm text-foreground">
                <span className="font-semibold text-primary">{idx + 1}.</span>
                <span className="leading-relaxed">{step}</span>
              </li>
            ))}
          </ol>
        ) : (
          <p className="mt-2 text-sm leading-relaxed text-foreground">
            {analysis.action_required || "Review the notice details carefully and maintain a copy for your records."}
          </p>
        )}
      </div>

      {/* Footer Disclaimer & Upload Another Notice */}
      <div className="pt-2 text-center space-y-3">
        <p className="text-xs text-muted-foreground">
          This explanation is for informational purposes only and is not legal advice.
        </p>

        <div>
          <button
            type="button"
            id="upload-another-button"
            onClick={onStartOver}
            className="inline-flex items-center justify-center rounded-full bg-primary px-6 py-2.5 font-display text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
          >
            Upload another notice
          </button>
        </div>
      </div>
    </div>
  );
}
