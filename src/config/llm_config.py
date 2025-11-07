import os
from dataclasses import dataclass
from typing import Any, List, Optional
import logging

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage as LangChainAIMessage

load_dotenv()

logger = logging.getLogger(__name__)


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
    """Provider-agnostic LLM wrapper using LangChain's init_chat_model().

    Supports three providers with automatic fallback:
    - NVIDIA NIM (nvidia_ai_endpoints)
    - OpenAI (openai)
    - Google Gemini (google_genai)
    
    Key features:
    - Pure LangChain ecosystem (no OpenAI SDK)
    - Automatic fallback if primary provider fails
    - Runtime provider switching via config
    - Backward compatible invoke() interface
    """

    def __init__(
        self,
        provider: str = "openai",
        temperature: float = None,  # None = use model default
        openai_model: str = "gpt-4o-mini",
        gemini_model: str = "gemini-2.5-pro",
        nvidia_model: str = "qwen3-next-80b-a3b-instruct",
        max_output_tokens: int = 8192,
        request_timeout: int = 120,
    ) -> None:
        self.provider = provider.lower().strip()
        self.temperature = temperature  # Can be None
        self.openai_model = os.getenv("OPENAI_MODEL", openai_model)
        self.gemini_model = os.getenv("GEMINI_MODEL", gemini_model)
        self.nvidia_model = os.getenv("NVIDIA_MODEL", nvidia_model)
        self.max_output_tokens = max_output_tokens
        self.request_timeout = request_timeout

        # Initialize the chat model with fallback support
        self._init_chat_model()

    def _init_chat_model(self) -> None:
        """Initialize LangChain chat model with fallback support."""
        
        # Determine provider and model based on configuration
        provider_map = {
            "nvidia": ("nvidia", self.nvidia_model),
            "openai": ("openai", self.openai_model),
            "gemini": ("google_genai", self.gemini_model),
            "google": ("google_genai", self.gemini_model),  # Alias
        }
        
        if self.provider not in provider_map:
            logger.warning(f"Unknown provider '{self.provider}', defaulting to 'openai'")
            self.provider = "openai"
        
        provider_name, model_name = provider_map[self.provider]
        
        # Prepare model initialization kwargs
        kwargs = {
            "model": model_name,
            "model_provider": provider_name,
            "timeout": self.request_timeout,
            "max_tokens": self.max_output_tokens,
        }
        
        # Only add temperature if specified (some models don't support it)
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        
        # Try to initialize the primary provider
        try:
            logger.info(f"Initializing {provider_name} with model {model_name}")
            self.chat_model = init_chat_model(**kwargs)
            self.active_provider = self.provider
            logger.info(f"✓ Successfully initialized {self.active_provider}")
            return
        except Exception as e:
            logger.warning(f"Failed to initialize {self.provider}: {e}")
        
        # Fallback logic: try other available providers
        # Order: OpenAI → Gemini → NVIDIA (as documented in ENV_VARS.md)
        fallback_order = ["openai", "gemini", "nvidia"]
        # Remove the failed primary provider from fallback list
        fallback_order = [p for p in fallback_order if p != self.provider]
        
        for fallback_provider in fallback_order:
            if fallback_provider not in provider_map:
                continue
            
            fallback_provider_name, fallback_model = provider_map[fallback_provider]
            
            # Check if API key is available for fallback provider
            api_key_map = {
                "nvidia": "NVIDIA_API_KEY",
                "openai": "OPENAI_API_KEY",
                "gemini": "GOOGLE_API_KEY",
            }
            
            api_key_env = api_key_map.get(fallback_provider)
            if not api_key_env or not os.getenv(api_key_env):
                logger.debug(f"Skipping {fallback_provider}: no API key found ({api_key_env})")
                continue
            
            try:
                logger.info(f"Attempting fallback to {fallback_provider_name} ({fallback_model})")
                fallback_kwargs = {
                    "model": fallback_model,
                    "model_provider": fallback_provider_name,
                    "timeout": self.request_timeout,
                    "max_tokens": self.max_output_tokens,
                }
                
                if self.temperature is not None:
                    fallback_kwargs["temperature"] = self.temperature
                
                self.chat_model = init_chat_model(**fallback_kwargs)
                self.active_provider = fallback_provider
                logger.info(f"✓ Fallback successful: now using {self.active_provider}")
                return
            except Exception as e:
                logger.warning(f"Fallback to {fallback_provider} failed: {e}")
                continue
        
        # If all providers fail, raise error
        raise RuntimeError(
            f"Failed to initialize any LLM provider. Tried: {self.provider}, {', '.join(fallback_order)}. "
            f"Please check your API keys (NVIDIA_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY) in .env file."
        )

    def invoke(self, input_data: Any) -> _AIMessage:
        """Unified invoke accepting either str or LangChain-style messages list.
        
        Args:
            input_data: Can be:
                - str: Plain text prompt
                - List[HumanMessage]: LangChain message format
                - Any other format (will be coerced to string)
        
        Returns:
            _AIMessage with content field containing the response
        """
        try:
            # Convert input to appropriate format
            if isinstance(input_data, str):
                # Direct string input
                messages = [HumanMessage(content=input_data)]
            elif isinstance(input_data, list):
                # Already a list of messages or needs conversion
                if input_data and hasattr(input_data[0], "content"):
                    # Already LangChain messages
                    messages = input_data
                else:
                    # Convert list to text and wrap in HumanMessage
                    text = _coerce_to_text(input_data)
                    messages = [HumanMessage(content=text)]
            else:
                # Coerce to text and wrap
                text = _coerce_to_text(input_data)
                messages = [HumanMessage(content=text)]
            
            # Invoke the chat model
            result = self.chat_model.invoke(messages)
            
            # Extract content from result
            if isinstance(result, LangChainAIMessage):
                content = result.content
            else:
                content = str(getattr(result, "content", result))
            
            return _AIMessage(content=str(content))
            
        except Exception as e:
            logger.error(f"Error invoking {self.active_provider}: {e}")
            raise RuntimeError(f"LLM invocation failed: {e}")


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
    nvidia_model=CONVERTER_MODEL if CONVERTER_PROVIDER == "nvidia" else "qwen3-next-80b-a3b-instruct",
    max_output_tokens=16000  # Large output for JSON
)

logger.info(f"LLM Configuration: Primary={model.active_provider}, Converter={converter_model.active_provider}")
