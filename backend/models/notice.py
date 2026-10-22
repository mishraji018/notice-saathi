from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class ExplanationPoint(BaseModel):
    text: str
    source_sentence: Optional[str] = None


class Helpline(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None


DocumentCategory = Literal["government_notice", "government_document_other", "not_government"]


class NoticeData(BaseModel):
    document_category: DocumentCategory = "government_notice"
    notice_type: Optional[str] = None
    detected_type: Optional[str] = None
    authority: Optional[str] = None
    deadline: Optional[str] = None
    amount: Optional[str] = None
    action_required: Optional[str] = None
    urgency_level: Optional[Literal["high", "medium", "low"]] = None
    scam_likelihood: Literal["high", "medium", "low", "none"] = "none"
    scam_reasons: List[str] = Field(default_factory=list)
    explanation_points: List[ExplanationPoint] = Field(default_factory=list)
    raw_text: Optional[str] = None
    helpline: Optional[Helpline] = None
    is_high_risk: bool = False


class AnalyzeResponse(BaseModel):
    status: Literal["success", "error"] = "success"
    data: Optional[NoticeData] = None
    message: Optional[str] = None


class ReexplainRequest(BaseModel):
    raw_text: str
    language: Literal["en", "hi"] = "en"
