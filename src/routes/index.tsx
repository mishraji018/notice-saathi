import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

import { analyzeNotice } from "@/lib/api";
import type { NoticeAnalysis } from "@/lib/types";
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
          "Upload a government notice and get a simple explanation — what it means, what to do, and key deadlines.",
      },
    ],
  }),
  component: Index,
});

function Index() {
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<NoticeAnalysis | null>(null);

  const handleFileSelected = async (file: File) => {
    setStatus("loading");
    setErrorMessage(null);
    try {
      const data = await analyzeNotice(file, "en");
      setAnalysis(data);
      setStatus("success");
    } catch (err: any) {
      setErrorMessage(
        err?.message || "Could not process this document. Please check the file and try again."
      );
      setStatus("error");
    }
  };

  const startOver = () => {
    setStatus("idle");
    setAnalysis(null);
    setErrorMessage(null);
  };

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="mx-auto flex w-full max-w-3xl items-center justify-between px-4 py-3.5">
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
            <span className="font-display text-xl font-bold tracking-tight text-foreground">
              Notice Saathi
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-16 pt-8">
        {status === "idle" && (
          <div className="mb-6 text-center space-y-1">
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Government notices, explained in plain words
            </h1>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Upload your notice to get a simple breakdown of what it says, key dates, and what action to take.
            </p>
          </div>
        )}

        {/* 1. Upload & Analyze State */}
        {status === "idle" && (
          <UploadCard onFileSelected={handleFileSelected} />
        )}

        {/* 2. Loading State */}
        {status === "loading" && (
          <LoadingState language="en" />
        )}

        {/* 3. Results Screen with 5 simple cards */}
        {status === "success" && analysis && (
          <ResultsView analysis={analysis} onStartOver={startOver} />
        )}

        {/* 4. Friendly Error State */}
        {status === "error" && (
          <div className="rounded-2xl border border-destructive/25 bg-destructive/10 p-6 text-center space-y-4" role="alert">
            <div className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-destructive/20 text-destructive text-lg font-bold">
              !
            </div>
            <div>
              <h2 className="font-display text-base font-bold text-destructive">
                Unable to Analyze Notice
              </h2>
              <p className="mt-1 text-sm text-muted-foreground max-w-md mx-auto">
                {errorMessage || "We couldn't read that notice. Please try again with a clearer photo or PDF."}
              </p>
            </div>
            <button
              type="button"
              onClick={startOver}
              className="inline-flex items-center rounded-full bg-primary px-6 py-2.5 font-display text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 transition-colors"
            >
              Upload another notice
            </button>
          </div>
        )}
      </main>

      {/* 5. Footer */}
      <footer className="border-t border-border py-4 text-center">
        <p className="px-4 text-xs text-muted-foreground">
          Notice Saathi · Prototype version · This tool does not provide legal advice.
        </p>
      </footer>
    </div>
  );
}
