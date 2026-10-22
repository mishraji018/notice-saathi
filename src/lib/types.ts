export type Language = "en" | "hi";
export type UrgencyLevel = "high" | "medium" | "low";
export type ScamLikelihood = "high" | "medium" | "low" | "none";

export interface ExplanationPoint {
  text: string;
  source_sentence: string;
}

export type DocumentCategory = "government_notice" | "government_document_other" | "not_government";

export interface NoticeAnalysis {
  document_category?: DocumentCategory;
  notice_type: string | null;
  detected_type?: string | null;
  authority: string | null;
  deadline: string | null;
  amount: string | null;
  action_required: string | null;
  urgency_level: UrgencyLevel | null;
  scam_likelihood: ScamLikelihood;
  scam_reasons: string[];
  explanation_points: ExplanationPoint[];
  raw_text: string;
  helpline: { name: string; number: string } | null;
  is_high_risk: boolean;
}


export interface AnalyzeResponse {
  status: "success" | "error";
  data?: NoticeAnalysis;
  message?: string;
}
