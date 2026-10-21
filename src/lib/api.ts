import type { AnalyzeResponse, Language, NoticeAnalysis } from "./types";
import { t } from "./strings";

/**
 * Base URL of the backend that implements the contract documented in README.md.
 * Override with VITE_API_BASE_URL; defaults to a local backend.
 */
const API_BASE_URL: string =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ??
  (import.meta.env["NEXT_PUBLIC_API_BASE_URL"] as string | undefined) ??
  "http://localhost:8000";

/** POST multipart/form-data to /analyze with "file" and "language" (35s timeout + offline guard). */
export async function analyzeNotice(file: File, language: Language): Promise<NoticeAnalysis> {
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    throw new Error(t(language, "offlineError"));
  }

  const body = new FormData();
  body.append("file", file);
  body.append("language", language);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  try {
    const res = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body,
      signal: controller.signal,
    });
    const json = (await res.json().catch(() => null)) as AnalyzeResponse | null;
    if (!res.ok || json?.status !== "success" || !json?.data) {
      throw new Error(json?.message ?? t(language, "analyzeError"));
    }
    return json.data;
  } catch (err: any) {
    if (err?.name === "AbortError" || controller.signal.aborted) {
      throw new Error(t(language, "timeoutError"));
    }
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new Error(t(language, "offlineError"));
    }
    if (err instanceof TypeError) {
      throw new Error(t(language, "analyzeError"));
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

/** POST JSON to /reexplain — used when switching language without re-uploading (35s timeout). */
export async function reExplain(rawText: string, language: Language): Promise<NoticeAnalysis> {
  if (typeof navigator !== "undefined" && !navigator.onLine) {
    throw new Error(t(language, "offlineError"));
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  try {
    const res = await fetch(`${API_BASE_URL}/reexplain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText, language }),
      signal: controller.signal,
    });
    const json = (await res.json().catch(() => null)) as AnalyzeResponse | null;
    if (!res.ok || json?.status !== "success" || !json?.data) {
      throw new Error(json?.message ?? "Re-explanation failed");
    }
    return json.data;
  } catch (err: any) {
    if (err?.name === "AbortError" || controller.signal.aborted) {
      throw new Error(t(language, "timeoutError"));
    }
    if (typeof navigator !== "undefined" && !navigator.onLine) {
      throw new Error(t(language, "offlineError"));
    }
    if (err instanceof TypeError) {
      throw new Error(t(language, "analyzeError"));
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

let currentAudio: HTMLAudioElement | null = null;

export function stopSpeaking(): void {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  if (typeof speechSynthesis !== "undefined") speechSynthesis.cancel();
}

/** GET /speak?text=...&language=... and play the returned audio. Falls back to the browser's built-in speech. */
export async function speakText(text: string, language: Language): Promise<void> {
  stopSpeaking();
  try {
    const url = `${API_BASE_URL}/speak?text=${encodeURIComponent(text)}&language=${language}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Speak request failed");
    const blob = await res.blob();
    const audio = new Audio(URL.createObjectURL(blob));
    currentAudio = audio;
    audio.onended = () => {
      if (currentAudio === audio) currentAudio = null;
    };
    await audio.play();
  } catch {
    if (typeof speechSynthesis !== "undefined") {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === "hi" ? "hi-IN" : "en-IN";
      speechSynthesis.speak(utterance);
    }
  }
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function buildLocalIcs(title: string, deadline: string): string {
  const parsed = new Date(deadline);
  const target = Number.isNaN(parsed.getTime()) ? new Date(Date.now() + 7 * 86_400_000) : parsed;
  const start = new Date(target);
  start.setHours(9, 0, 0, 0);
  const end = new Date(start.getTime() + 30 * 60_000);
  const fmt = (d: Date) => d.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const uid = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Notice Saathi//EN",
    "BEGIN:VEVENT",
    `UID:${uid}@notice-saathi`,
    `DTSTAMP:${fmt(new Date())}`,
    `DTSTART:${fmt(start)}`,
    `DTEND:${fmt(end)}`,
    `SUMMARY:${title.replace(/\r?\n/g, " ")}`,
    "DESCRIPTION:Reminder created by Notice Saathi",
    "END:VEVENT",
    "END:VCALENDAR",
  ].join("\r\n");
}

/** GET /reminder.ics?title=...&deadline=...&language=... and download the calendar file. Falls back to a locally generated .ics. */
export async function downloadReminder(
  title: string,
  deadline: string,
  language: Language,
): Promise<void> {
  const url =
    `${API_BASE_URL}/reminder.ics?title=${encodeURIComponent(title)}` +
    `&deadline=${encodeURIComponent(deadline)}&language=${encodeURIComponent(language)}`;
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Reminder request failed");
    triggerDownload(await res.blob(), "notice-reminder.ics");
  } catch {
    triggerDownload(new Blob([buildLocalIcs(title, deadline)], { type: "text/calendar" }), "notice-reminder.ics");
  }
}
