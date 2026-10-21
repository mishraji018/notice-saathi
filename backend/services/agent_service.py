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
Your mission is to analyze raw OCR text from official government notices, court summons, utility bills, tax demands, or potential scam documents, and explain them in plain language that an everyday citizen can understand.

You must follow these rules strictly:
1. OCR Robustness: The raw text comes from OCR and may have noise, missing punctuation, typos, or irregular line breaks. Reconstruct meaning from context.
2. Classification: Accurately identify the notice_type (e.g. "Income Tax Notice — Section 142(1)", "Electricity Disconnection Notice", "Court Summons", "Traffic Challan", "Bank Loan Demand", "GST Notice", "Municipal Property Tax Demand").
3. Extraction:
   - authority: Full name of the issuing department, government body, or organization.
   - deadline: The compliance or payment deadline date/time limit if specified (e.g. "15 November 2026"), otherwise null.
   - amount: Total amount demanded, penalty, or fee including currency (e.g. "₹48,200"), otherwise null.
   - action_required: Clear, direct statement of what the recipient must do next to resolve this notice.
4. Urgency Assessment:
   - "high": Immediate consequence threatened (e.g., legal arrest, court warrant, power disconnection, bank freeze, heavy recurring penalty, or deadline within 7 days).
   - "medium": Formal compliance required, but standard response time is provided (e.g., 15-30 days to file response).
   - "low": Purely informational, acknowledgement, or routine record.
5. Scam Likelihood Assessment:
   - Check for scam indicators:
     * Demands payment to personal UPI IDs (e.g. ending in @okaxis, @ybl, @paytm) or personal savings accounts rather than official government portals or challans.
     * Unusually threatening, unprofessional language ("Police will arrest you in 2 hours").
     * Absence of mandatory official identifiers (DIN, PAN, Notice Reference Number, official seal).
     * Suspicious contact details (e.g. @gmail.com or @yahoo.com for government officials).
     * Extreme artificial urgency demanding immediate payment through gift cards or transfers.
   - Set scam_likelihood to "high", "medium", "low", or "none".
   - If not "none", list the concrete scam_reasons explaining why.
6. Simplified Explanation Points (Class 6 Reading Level):
   - Provide 3 to 5 clear, jargon-free bullet points explaining: (a) What this notice is about, (b) Why you received it, and (c) What will happen if you do or don't respond.
   - For EACH point, you MUST provide 'source_sentence', which is an EXACT, verbatim substring from raw_text supporting that point.
7. Language Support:
   - If target language is "hi", write 'notice_type', 'action_required', and all 'explanation_points.text' in clear Hindi (Devanagari script). Keep 'source_sentence' in its original language as it appears in raw_text.
   - If target language is "en", write in simple English.
8. Official Helpline:
   - If this is a standard Indian notice type with a verified public helpline, provide it (e.g. Income Tax: {"name": "Aaykar Sampark Kendra", "number": "1800-180-1961"}, National Consumer Helpline: {"name": "NCH", "number": "1915"}, Cyber Crime: {"name": "Cyber Crime Helpline", "number": "1930"}). Otherwise null.
9. Risk Flag:
   - Set is_high_risk to true if urgency_level is "high" OR scam_likelihood is "high" or "medium"; otherwise false.
10. Non-Notice Documents: If the document is clearly NOT an official notice, government order, utility bill, summons, or legal/financial communication (e.g., a personal selfie, a meme, receipt, or random note):
   - Set notice_type to "Unrecognized Document" (or "अपरिचित दस्तावेज़" in Hindi).
   - Set urgency_level to "low".
   - Set scam_likelihood to "none".
   - Set action_required and explanation_points to politely inform the user that this does not appear to be an official notice.
"""

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "notice_type": {
            "type": "string",
            "description": "Classified type of notice in target language (e.g. 'Income Tax Notice — Section 142(1)').",
        },
        "authority": {
            "type": ["string", "null"],
            "description": "Full official issuing department or authority name, or null if unknown.",
        },
        "deadline": {
            "type": ["string", "null"],
            "description": "Explicit due date or time limit for compliance (e.g. '15 November 2026'), or null.",
        },
        "amount": {
            "type": ["string", "null"],
            "description": "Total monetary amount demanded or penalty with currency symbol (e.g. '₹48,200'), or null.",
        },
        "action_required": {
            "type": "string",
            "description": "Concise, plain-language directive stating exactly what the citizen must do.",
        },
        "urgency_level": {
            "type": "string",
            "enum": ["high", "medium", "low"],
            "description": "Level of time-sensitivity and severity of consequences.",
        },
        "scam_likelihood": {
            "type": "string",
            "enum": ["high", "medium", "low", "none"],
            "description": "Assessed likelihood of the notice being fraudulent or a phishing scam.",
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
                        "description": "Simple 6th-grade explanation point in target language.",
                    },
                    "source_sentence": {
                        "type": ["string", "null"],
                        "description": "Exact verbatim substring from raw_text supporting this point.",
                    },
                },
                "required": ["text", "source_sentence"],
            },
            "description": "3 to 5 simple, accessible explanatory bullet points.",
        },
        "helpline": {
            "type": ["object", "null"],
            "properties": {
                "name": {"type": "string"},
                "number": {"type": "string"},
            },
            "required": ["name", "number"],
            "description": "Verified Indian helpline if known, else null.",
        },
        "is_high_risk": {
            "type": "boolean",
            "description": "True if urgency is high or scam_likelihood is high/medium.",
        },
    },
    "required": [
        "notice_type",
        "action_required",
        "urgency_level",
        "scam_likelihood",
        "scam_reasons",
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

        tool_call_input["raw_text"] = raw_text

        try:
            return NoticeData(**tool_call_input)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to parse structured notice data from AI output: {str(e)}",
            )

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

        tool_call_input["raw_text"] = raw_text

        try:
            return NoticeData(**tool_call_input)
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
