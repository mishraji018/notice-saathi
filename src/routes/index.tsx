import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { analyzeNotice, reExplain } from "@/lib/api";
import { t } from "@/lib/strings";
import type { Language, NoticeAnalysis } from "@/lib/types";
import { LanguageToggle } from "@/components/LanguageToggle";
import { LoadingState } from "@/components/LoadingState";
import { ResultsView } from "@/components/ResultsView";
import { UploadCard } from "@/components/UploadCard";

type Status = "idle" | "loading" | "success" | "error";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Notice Saathi — Government notices, explained in plain words" },
      {
        name: "description",
        content:
          "Upload a government notice and get a simple explanation in English or Hindi — what it means, what to do, and what to watch out for.",
      },
      { property: "og:title", content: "Notice Saathi — Government notices, explained in plain words" },
      {
        property: "og:description",
        content:
          "Upload a government notice and get a simple explanation in English or Hindi — what it means, what to do, and what to watch out for.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  const [language, setLanguage] = useState<Language>("en");
  const [status, setStatus] = useState<Status>("idle");
  const [analysis, setAnalysis] = useState<NoticeAnalysis | null>(null);

  const handleLanguageChange = async (next: Language) => {
    setLanguage(next);
    if (status === "success" && analysis) {
      // Re-explain the same notice in the new language without re-uploading.
      try {
        setAnalysis(await reExplain(analysis.raw_text, next));
      } catch {
        // Keep the current explanation; the UI text still switches.
      }
    }
  };

  const handleFileSelected = async (file: File) => {
    setStatus("loading");
    try {
      setAnalysis(await analyzeNotice(file, language));
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  const startOver = () => {
    setStatus("idle");
    setAnalysis(null);
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border bg-background/95">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary shadow-sm" aria-hidden="true">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5 text-primary-foreground"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <path d="M14 2v6h6" />
                <path d="M9 13h6M9 17h4" />
              </svg>
            </span>
            <span className="font-display text-xl font-bold text-foreground">{t(language, "appTitle")}</span>
          </div>
          <LanguageToggle language={language} onChange={handleLanguageChange} />
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8">
        <p className="mb-6 text-center font-display text-lg font-semibold text-muted-foreground">
          {t(language, "tagline")}
        </p>

        {status === "idle" && <UploadCard language={language} onFileSelected={handleFileSelected} />}

        {status === "loading" && <LoadingState language={language} />}

        {status === "success" && analysis && (
          <ResultsView analysis={analysis} language={language} onStartOver={startOver} />
        )}

        {status === "error" && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/10 p-6 text-center" role="alert">
            <p className="text-sm font-medium text-destructive">{t(language, "analyzeError")}</p>
            <button
              type="button"
              onClick={startOver}
              className="mt-4 inline-flex items-center rounded-full bg-primary px-5 py-2.5 font-display text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
            >
              {t(language, "uploadButton")}
            </button>
          </div>
        )}
      </main>

      <footer className="border-t border-border py-4">
        <p className="px-4 text-center text-xs text-muted-foreground">
          {t(language, "appTitle")} · {t(language, "tagline")}
        </p>
      </footer>
    </div>
  );
}
