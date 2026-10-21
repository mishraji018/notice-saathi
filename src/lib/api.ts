import type { AnalyzeResponse, Language, NoticeAnalysis } from "./types";
import { demoAnalysis } from "./demo";

/**
 * Base URL of the backend that implements the contract documented in README.md.
 * Override with VITE_API_BASE_URL; defaults to a local backend.
 * When the backend is unreachable the built-in demo analysis is returned so the
 * full flow stays usable.
 */
const API_BASE_URL: string = import.meta.env["VITE_API_BASE_URL"] ?? "http://localhost:8000";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function postFormAndParse(body: FormData, url: string): Promise<NoticeAnalysis> {
  const res = await fetch(url, { method: "POST", body });
  const json = (await res.json()) as AnalyzeResponse;
  if (!res.ok || json.status !== "success" || !json.data) {
    throw new Error(json.message ?? "Analysis failed");
  }
  return json.data;
}

/** POST multipart/form-data to /analyze with "file" and "language". */
export async function analyzeNotice(file: File, language: Language): Promise<NoticeAnalysis> {
  const body = new FormData();
  body.append("file", file);
  body.append("language", language);
  try {
    return await postFormAndParse(body, `${API_BASE_URL}/analyze`);
  } catch (err) {
    if (err instanceof TypeError) {
      // Network failure — no backend connected. Fall back to the demo analysis.
      await wait(1600);
      return demoAnalysis(language);
    }
    throw err;
  }
}

/** POST JSON to /reexplain — used when switching language without re-uploading. */
export async function reExplain(rawText: string, language: Language): Promise<NoticeAnalysis> {
  try {
    const res = await fetch(`${API_BASE_URL}/reexplain`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText, language }),
    });
    const json = (await res.json()) as AnalyzeResponse;
    if (!res.ok || json.status !== "success" || !json.data) {
      throw new Error(json.message ?? "Re-explanation failed");
    }
    return json.data;
  } catch (err) {
    if (err instanceof TypeError) {
      return demoAnalysis(language);
    }
    throw err;
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
