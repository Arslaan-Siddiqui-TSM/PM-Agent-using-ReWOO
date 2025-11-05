import os
from dataclasses import dataclass
from typing import Any, List

from dotenv import load_dotenv

# Optional imports guarded at runtime
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception:  # pragma: no cover - optional dependency at runtime
    ChatGoogleGenerativeAI = None  # type: ignore

try:
    from openai import OpenAI  # OpenAI Python SDK >=1.0
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


load_dotenv()


def _coerce_to_text(input_data: Any) -> str:
    """Best-effort conversion of various invoke() inputs to a single user text string.

    Supports:
    - str
    - List of objects with .content (e.g., LangChain HumanMessage[])
    - Any other object (fallback to str())
    """
    if isinstance(input_data, str):
        return input_data
    if isinstance(input_data, list):
        parts: List[str] = []
        for item in input_data:
            content = getattr(item, "content", None)
            parts.append(str(content if content is not None else item))
        return "\n\n".join(parts)
    return str(input_data)


@dataclass
class _AIMessage:
    """Minimal message-like container to mirror LangChain's result.content."""
    content: str


class UnifiedLLM:
    """Provider-agnostic LLM wrapper exposing a simple invoke() method.

    - Primary: OpenAI reasoning models (o4-mini by default)
    - Fallback: Google Gemini via LangChain if configured/required
    """

    def __init__(
        self,
        provider: str = "openai",
        temperature: float = None,  # None = use model default
        openai_model: str = "o4-mini",
        gemini_model: str = "gemini-2.5-pro",
        max_output_tokens: int = 8192,
        request_timeout: int = 120,
    ) -> None:
        self.provider = provider.lower().strip()
        self.temperature = temperature  # Can be None
        self.openai_model = os.getenv("OPENAI_MODEL", openai_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", gemini_model)
        self.max_output_tokens = max_output_tokens
        self.request_timeout = request_timeout

        self._init_clients()

    def _init_clients(self) -> None:
        self.openai_client = None
        self.gemini_chat = None

        if self.provider == "openai":
            if OpenAI is None:
                raise RuntimeError(
                    "OpenAI SDK not installed. Please add 'openai' to requirements and set OPENAI_API_KEY."
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                # Graceful fallback to Gemini if available
                google_api_key = os.getenv("GOOGLE_API_KEY")
                if ChatGoogleGenerativeAI is not None and google_api_key:
                    self.provider = "gemini"
                    self.gemini_chat = ChatGoogleGenerativeAI(
                        model=self.gemini_model,
                        temperature=self.temperature,
                        google_api_key=google_api_key,
                        max_retries=6,
                        request_timeout=self.request_timeout,
                        max_output_tokens=self.max_output_tokens,
                    )
                    return
                raise RuntimeError("Missing OPENAI_API_KEY in environment.")
            # OpenAI SDK picks API key from env automatically; explicit client for clarity
            self.openai_client = OpenAI()
        elif self.provider in ("gemini", "google"):  # allow synonyms
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError(
                    "langchain-google-genai not installed. Install it or switch provider to OpenAI."
                )
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise RuntimeError("Missing GOOGLE_API_KEY in environment.")
            # Keep LangChain chat model for backward compatibility
            self.gemini_chat = ChatGoogleGenerativeAI(
                model=self.gemini_model,
                temperature=self.temperature,
                google_api_key=google_api_key,
                max_retries=6,
                request_timeout=self.request_timeout,
                max_output_tokens=self.max_output_tokens,
            )
        else:
            # Default to OpenAI if unknown provider
            if OpenAI is None:
                raise RuntimeError(
                    "Unknown LLM provider and OpenAI SDK missing. Install 'openai' or set LLM_PROVIDER."
                )
            self.openai_client = OpenAI()
            self.provider = "openai"

    def _invoke_openai(self, prompt: str) -> _AIMessage:
        """Invoke OpenAI models. Uses Responses API for reasoning models by default."""
        assert self.openai_client is not None
        model_name = self.openai_model

        # Heuristic: use Responses API for o* reasoning models, else Chat Completions
        if model_name.startswith("o"):
            # Responses API for reasoning models (o4, o4-mini, o3, etc.)
            # NOTE: Many reasoning models do not support 'temperature' parameter.
            # Do NOT pass temperature here to avoid 400 invalid_request_error.
            resp = self.openai_client.responses.create(
                model=model_name,
                input=prompt,
            )
            # Robust extraction across SDK versions
            text = getattr(resp, "output_text", None)
            if not text:
                try:
                    # Fallback: concatenate content parts
                    parts = []
                    for item in getattr(resp, "output", []) or []:
                        # Each item may have content list with text
                        for c in getattr(item, "content", []) or []:
                            if getattr(c, "type", "") == "output_text":
                                parts.append(getattr(c, "text", ""))
                            else:
                                parts.append(getattr(c, "text", ""))
                    text = "".join(parts) or str(resp)
                except Exception:
                    text = str(resp)
            return _AIMessage(content=str(text))
        else:
            # Chat Completions API for non-reasoning models
            # Only pass temperature if specified (not None)
            kwargs = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
            }
            if self.temperature is not None:
                kwargs["temperature"] = self.temperature
            
            resp = self.openai_client.chat.completions.create(**kwargs)
            text = (resp.choices[0].message.content if resp.choices else "")
            return _AIMessage(content=str(text))

    def _invoke_gemini(self, input_data: Any) -> _AIMessage:
        assert self.gemini_chat is not None
        result = self.gemini_chat.invoke(input_data)
        return _AIMessage(content=str(getattr(result, "content", result)))

    def invoke(self, input_data: Any) -> _AIMessage:
        """Unified invoke accepting either str or LangChain-style messages list."""
        if self.provider in ("gemini", "google"):
            # For Gemini, preserve original input to keep LangChain behavior
            return self._invoke_gemini(input_data)

        # Default/OpenAI path: coerce to a single user prompt string
        prompt = _coerce_to_text(input_data)
        return self._invoke_openai(prompt)


# Read provider preference from environment, default to OpenAI
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()

# Converter-specific configuration
CONVERTER_PROVIDER = os.getenv("CONVERTER_PROVIDER", LLM_PROVIDER).lower()
CONVERTER_MODEL = os.getenv("CONVERTER_MODEL", "gpt-4o-mini")  # Default to mini model
USE_LLM_CONVERTER = os.getenv("USE_LLM_CONVERTER", "true").lower() in ("true", "1", "yes")

# Single export used across the app (main model for analysis)
# Don't specify temperature - use model defaults
model = UnifiedLLM(provider=LLM_PROVIDER, temperature=None)

# Separate converter model for MD → JSON conversion (mini model)
# Note: temperature=None to use model defaults - avoids compatibility issues
converter_model = UnifiedLLM(
    provider=CONVERTER_PROVIDER,
    temperature=None,  # Use model default
    openai_model=CONVERTER_MODEL if CONVERTER_PROVIDER == "openai" else "gpt-4o-mini",
    gemini_model=CONVERTER_MODEL if CONVERTER_PROVIDER in ("gemini", "google") else "gemini-1.5-flash",
    max_output_tokens=16000  # Large output for JSON
)

