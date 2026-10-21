export type Language = "en" | "hi";
export type UrgencyLevel = "high" | "medium" | "low";
export type ScamLikelihood = "high" | "medium" | "low" | "none";

export interface ExplanationPoint {
  text: string;
  source_sentence: string;
}

export interface NoticeAnalysis {
  notice_type: string;
  authority: string | null;
  deadline: string | null;
  amount: string | null;
  action_required: string;
  urgency_level: UrgencyLevel;
  scam_likelihood: ScamLikelihood;
  scam_reasons: string[];
  explanation_points: ExplanationPoint[];
  raw_text: string;
  helpline: { name: string; number: string } | null;
  is_high_risk: boolean;
  /** Set only when the result came from the built-in demo (no backend connected). */
  is_demo?: boolean;
}

export interface AnalyzeResponse {
  status: "success" | "error";
  data?: NoticeAnalysis;
  message?: string;
}
