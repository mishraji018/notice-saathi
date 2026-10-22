"""
AI Agent Service for Notice Saathi.
Uses Groq (openai/gpt-oss-120b) as the primary LLM provider (with Anthropic Claude fallback)
to analyze raw OCR text of notices, classify them, extract key facts, assess urgency & scam likelihood,
and explain them in simple terms.
"""

import os
import json
import logging
from typing import Literal, Dict, Any, Optional
from fastapi import HTTPException, status

logger = logging.getLogger("notice_saathi.agent")

try:
    from backend.models.notice import NoticeData, ExplanationPoint, Helpline
except ModuleNotFoundError:
    from models.notice import NoticeData, ExplanationPoint, Helpline

SYSTEM_PROMPT = """You are an expert Indian legal document analyst and consumer protection AI for "Notice Saathi".
Your mission is to analyze raw OCR text and classify the document into one of three distinct categories, extract key details, and explain it clearly in plain language.

You must follow these rules strictly:
1. OCR Robustness: The raw text comes from OCR and may have noise, missing punctuation, typos, or irregular line breaks. Reconstruct meaning from context.

2. Document Categorization (document_category):
   Classify the document into EXACTLY one of these three categories:
   - "government_notice": Official notices, court summons, tax demands (Income Tax, GST, Municipal), electricity/utility disconnection warnings, traffic challans, arrest/bailable warrants, or regulatory orders issued by government, courts, police, or statutory regulators.
     CRITICAL RULE FOR SAMPLES / DUMMY / FICTIONAL NOTICES:
     Users frequently test this platform with sample, mock, draft, template, practice, educational, or fictional notices (such as a sample GST show cause notice, dummy Income Tax letter, or mock summons with placeholder names/amounts).
     You MUST ALWAYS classify ANY sample, mock, draft, template, or fictional government notice as "government_notice".
     Analyze and explain its legal sections, demands, deadlines, and required actions just like an official notice. NEVER reject or classify sample/fictional notices as "not_government".
   - "government_document_other": Documents issued by or related to the government that are NOT notices and do NOT demand compliance or urgent action (e.g., scholarship application/registration slips, tax payment receipts, Aadhaar/PAN acknowledgement receipts, birth/caste certificates, scheme enrollment letters, government job registration slips).
   - "not_government": ONLY documents that are completely unrelated to government or legal administration, such as technical programming tutorials (e.g., Apache Spark, Python code), academic homework, personal chat screenshots, selfies, commercial product user manuals, or food recipes.

3. Naming and Labels:
   - NEVER use the label "Unrecognized Document".
   - If document_category is "government_notice": Set 'notice_type' to a clear, specific name (e.g. "Income Tax Notice — Section 142(1)", "GST Demand Notice", "Traffic E-Challan").
   - If document_category is "government_document_other": Set 'notice_type' to a meaningful document title (e.g. "Scholarship Registration Slip", "Aadhaar Card Acknowledgement", "Property Tax Receipt").
   - If document_category is "not_government": 'notice_type' MUST BE null. Instead, set 'detected_type' to what kind of document it is (e.g. "Technical Tutorial", "Academic Lab Guide", "Private Company Bill", "Personal Chat Screenshot").

4. Category-Specific Fields:
   - For "government_notice":
     * authority: Official issuing department or organization.
     * deadline: Compliance date if stated (e.g. "18 November 2026"), otherwise null.
     * amount: Total demand or penalty amount (e.g. "₹54,300"), otherwise null.
     * action_required: Clear directive of what the citizen must do next.
     * urgency_level: "high", "medium", or "low".
   - For "government_document_other":
     * authority: Issuing department or body if known, else null.
     * deadline: Must be null.
     * amount: Must be null.
     * action_required: "Keep this document safe for your records. No action or reply is required."
     * urgency_level: Must be null.
   - For "not_government":
     * notice_type: Must be null.
     * deadline: Must be null.
     * amount: Must be null.
     * urgency_level: Must be null.
     * action_required: null.
     * explanation_points: 1-2 points explaining what this document appears to be.

5. Simplified Explanation Points:
   - Provide 2 to 4 clear, jargon-free bullet points explaining the document.

6. Scam Likelihood Assessment:
   - Check for scam indicators. If not_government, set scam_likelihood to "none".
"""

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "document_category": {
            "type": "string",
            "enum": ["government_notice", "government_document_other", "not_government"],
            "description": "Classification into 3 categories: government_notice, government_document_other, or not_government.",
        },
        "notice_type": {
            "type": ["string", "null"],
            "description": "Specific notice or document name for government items. MUST be null if document_category is not_government.",
        },
        "detected_type": {
            "type": ["string", "null"],
            "description": "Descriptive type of document, especially when not_government (e.g. 'Technical Tutorial', 'Academic Lab Guide').",
        },
        "authority": {
            "type": ["string", "null"],
            "description": "Full official issuing department or authority name, or null.",
        },
        "deadline": {
            "type": ["string", "null"],
            "description": "Explicit due date for compliance, or null.",
        },
        "amount": {
            "type": ["string", "null"],
            "description": "Total monetary amount demanded, or null.",
        },
        "action_required": {
            "type": ["string", "null"],
            "description": "Concise plain-language directive stating what the citizen must do, or null.",
        },
        "urgency_level": {
            "type": ["string", "null"],
            "enum": ["high", "medium", "low", None],
            "description": "Urgency level for government_notice ('high', 'medium', 'low'), or null for non-notices.",
        },
        "scam_likelihood": {
            "type": "string",
            "enum": ["high", "medium", "low", "none"],
            "description": "Assessed likelihood of fraudulent notice.",
        },
        "scam_reasons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of specific red flags found, empty if none.",
        },
        "explanation_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Simple explanation point.",
                    },
                    "source_sentence": {
                        "type": ["string", "null"],
                        "description": "Exact verbatim substring from raw_text.",
                    },
                },
                "required": ["text"],
            },
            "description": "Simple explanatory bullet points.",
        },
        "helpline": {
            "type": ["object", "null"],
            "properties": {
                "name": {"type": "string"},
                "number": {"type": "string"},
            },
            "required": ["name", "number"],
            "description": "Verified helpline if known, else null.",
        },
        "is_high_risk": {
            "type": "boolean",
            "description": "True if urgency is high or scam_likelihood is high/medium.",
        },
    },
    "required": [
        "document_category",
        "explanation_points",
        "is_high_risk",
    ],
}



class AgentService:
    def __init__(self):
        self._provider: Optional[str] = None
        self._groq_client = None
        self._anthropic_client = None

    def _init_client(self):
        """Determine and initialize available LLM client (Groq preferred, Anthropic fallback)."""
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key and groq_api_key.strip():
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=groq_api_key.strip(), timeout=30.0)
                self._provider = "groq"
                self.model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
                logger.info(f"Using Groq LLM provider with model '{self.model_name}'")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_api_key and anthropic_api_key.strip():
            try:
                import anthropic
                self._anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key.strip(), timeout=30.0)
                self._provider = "anthropic"
                self.model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
                logger.info(f"Using Anthropic LLM provider with model '{self.model_name}'")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No LLM API key configured. Please set GROQ_API_KEY (or ANTHROPIC_API_KEY) in backend/.env.",
        )

    async def analyze_notice(
        self, raw_text: str, language: Literal["en", "hi"] = "en"
    ) -> NoticeData:
        """
        Analyze notice raw text and return a validated NoticeData instance.
        """
        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot analyze empty notice text.",
            )

        if not self._provider:
            self._init_client()

        lang_label = "Hindi (Devanagari script)" if language == "hi" else "English"
        user_prompt = (
            f"Please analyze this notice document.\n"
            f"Target Language for output: {lang_label} ({language})\n\n"
            f"--- BEGIN RAW NOTICE OCR TEXT ---\n"
            f"{raw_text}\n"
            f"--- END RAW NOTICE OCR TEXT ---"
        )

        if self._provider == "groq":
            return await self._call_groq(user_prompt, raw_text)
        else:
            return await self._call_anthropic(user_prompt, raw_text)

    async def _call_groq(self, user_prompt: str, raw_text: str) -> NoticeData:
        import groq

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "structured_notice_analysis",
                    "description": "Output the structured analysis of the notice document.",
                    "parameters": ANALYSIS_SCHEMA,
                },
            }
        ]

        try:
            response = self._groq_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "structured_notice_analysis"}},
                temperature=0.2,
            )
        except groq.APITimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The AI analysis service timed out (took longer than 30 seconds). Please try again.",
            )
        except groq.RateLimitError:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please wait a moment and try again.",
            )
        except groq.AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Groq API key. Please check GROQ_API_KEY in backend/.env.",
            )
        except groq.APIConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the AI analysis service. Please check your network and try again.",
            )
        except groq.APIStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Groq API error: {e.message}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to communicate with Groq AI agent: {str(e)}",
            )

        message = response.choices[0].message
        tool_call_input: Optional[Dict[str, Any]] = None

        if message.tool_calls:
            try:
                tool_call_input = json.loads(message.tool_calls[0].function.arguments)
            except Exception as e:
                logger.warning(f"Could not parse tool call arguments as JSON: {e}")

        if not tool_call_input and message.content:
            try:
                tool_call_input = json.loads(message.content)
            except Exception:
                pass

        if not tool_call_input:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI model did not return structured analysis data.",
            )
        return self._normalize_category_fields(tool_call_input, raw_text)

    async def _call_anthropic(self, user_prompt: str, raw_text: str) -> NoticeData:
        import anthropic

        analysis_tool = {
            "name": "structured_notice_analysis",
            "description": "Output the structured analysis of the notice document.",
            "input_schema": ANALYSIS_SCHEMA,
        }

        try:
            response = self._anthropic_client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=[analysis_tool],
                tool_choice={"type": "tool", "name": "structured_notice_analysis"},
                messages=[{"role": "user", "content": user_prompt}],
            )
        except anthropic.APITimeoutError:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="The AI analysis service timed out (took longer than 30 seconds). Please try again.",
            )
        except anthropic.RateLimitError:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests, please wait a moment and try again.",
            )
        except anthropic.AuthenticationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Anthropic API key. Please check ANTHROPIC_API_KEY in backend/.env.",
            )
        except anthropic.APIConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not connect to the AI analysis service. Please check your network and try again.",
            )
        except anthropic.APIStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Anthropic API error: {e.message}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to communicate with Anthropic AI agent: {str(e)}",
            )

        tool_call_input: Optional[Dict[str, Any]] = None
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name == "structured_notice_analysis":
                tool_call_input = content_block.input
                break

        if not tool_call_input:
            for content_block in response.content:
                if content_block.type == "text":
                    try:
                        tool_call_input = json.loads(content_block.text)
                        break
                    except Exception:
                        pass

        if not tool_call_input:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI model did not return structured analysis data.",
            )
        return self._normalize_category_fields(tool_call_input, raw_text)

    def _normalize_category_fields(self, data: Dict[str, Any], raw_text: str) -> NoticeData:
        data["raw_text"] = raw_text
        category = data.get("document_category", "government_notice")
        if category not in ("government_notice", "government_document_other", "not_government"):
            category = "government_notice"
            data["document_category"] = category

        # Safeguard: Never reject sample/fictional notices as not_government
        detected_type_str = (data.get("detected_type") or "").lower()
        notice_indicators = [
            "notice", "show cause", "gst", "tax", "challan", "summons", "court",
            "demand", "warrant", "assessment", "penalty", "revenue", "department",
            "tribunal", "compliance", "order", "inquiry"
        ]
        if category == "not_government" and any(ind in detected_type_str for ind in notice_indicators):
            logger.info(f"Overriding 'not_government' to 'government_notice' for detected_type: '{data.get('detected_type')}'")
            category = "government_notice"
            data["document_category"] = "government_notice"
            clean_title = data.get("detected_type", "")
            for word in ["(fictional)", "(Fictional)", "fictional", "Fictional", "sample", "Sample"]:
                clean_title = clean_title.replace(word, "").strip()
            data["notice_type"] = clean_title.title() or "Government Notice"
            if not data.get("urgency_level"):
                data["urgency_level"] = "medium"
            if not data.get("action_required"):
                data["action_required"] = "Review the notice details and submit required response or clarification."

        # Strictly enforce field rules by category
        if category == "not_government":
            data["notice_type"] = None
            data["urgency_level"] = None
            data["deadline"] = None
            data["amount"] = None
            data["scam_likelihood"] = "none"
            data["scam_reasons"] = []
            if not data.get("detected_type"):
                data["detected_type"] = "Non-Government Document"
        elif category == "government_document_other":
            data["urgency_level"] = None
            data["deadline"] = None
            data["amount"] = None
            data["scam_likelihood"] = "none"
            data["scam_reasons"] = []
            if not data.get("action_required"):
                data["action_required"] = "Keep this document safe for your records. No immediate compliance action is required."

        try:
            return NoticeData(**data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to parse structured notice data from AI output: {str(e)}",
            )

    async def reexplain_notice(
        self, raw_text: str, language: Literal["en", "hi"]
    ) -> NoticeData:
        """Re-explain notice in an alternate language."""
        return await self.analyze_notice(raw_text=raw_text, language=language)


# Global singleton instance
agent_service = AgentService()
