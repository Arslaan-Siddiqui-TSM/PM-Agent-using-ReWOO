"""
Feature Flags Configuration

Centralized feature toggles for optional enhancements.
All new features are disabled by default (opt-in).
"""

from pydantic_settings import BaseSettings
from typing import Optional


class FeatureFlags(BaseSettings):
    """Feature flags for optional capabilities."""
    
    # Docling configuration (PRIMARY document processor)
    docling_ocr_default: bool = False  # Default OFF for performance
    docling_table_mode: str = "fast"  # "fast" or "accurate"
    docling_export_format: str = "markdown"  # "markdown" or "text"
    
    # Kroki diagram generation (FREE - no API key needed!)
    kroki_url: str = "https://kroki.io"
    enable_diagram_generation: bool = False  # Opt-in feature
    
    # Performance settings
    max_file_size_mb: int = 50  # Maximum file size for upload
    parallel_workers: int = 4  # Thread pool size for CPU-bound tasks
    
    # Intelligent parsing configuration
    use_intelligent_parsing: bool = True  # Enable intelligent parser routing
    parsing_complexity_threshold: float = 0.3  # Complexity threshold (0.0-1.0)
    force_docling: bool = False  # Force Docling for all docs (debugging)
    
    # Hardcoded session mode (for fast development/testing)
    use_hardcoded_session: bool = False
    hardcoded_collection: str = "pm_agent_468e90d3"
    hardcoded_md_dir: str = "data/hardcoded_session/markdown"
    hardcoded_json_dir: str = "data/hardcoded_session/json"
    
    # Hardcoded feasibility mode (skip LLM calls for development/testing)
    use_hardcoded_feasibility: bool = False
    hardcoded_feasibility_thinking_file: str = "data/hardcoded_session/thinking_summary.md"
    hardcoded_feasibility_report_file: str = "data/hardcoded_session/feasibility_report.md"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global instance
feature_flags = FeatureFlags()