"""
Configuration for Document Intelligence System
"""

# Document Classification Settings
CLASSIFICATION_CONFIG = {
    # Minimum confidence threshold for accepting classification
    "min_confidence_threshold": 0.5,
    
    # Number of pages to sample for classification
    "sample_pages": 3,
    
    # Maximum characters per page for classification
    "max_chars_per_page": 2000,
    
    # Enable/disable caching
    "enable_caching": True,
    
    # Cache directory
    "cache_dir": "cache",
    
    # Cache expiration (days)
    "cache_expiration_days": 30
}

# Content Extraction Settings
EXTRACTION_CONFIG = {
    # Maximum document length for extraction (characters)
    "max_document_length": 20000,
    
    # Minimum extraction confidence threshold
    "min_extraction_confidence": 0.3,
    
    # Enable type-specific extraction strategies
    "enable_type_specific_extraction": True
}

# Document Analysis Settings
ANALYSIS_CONFIG = {
    # Expected document types for complete project
    "expected_document_types": [
        "functional_specification",
        "technical_specification",
        "requirements_document",
        "test_plan",
        "use_case"
    ],
    
    # Critical information categories
    "critical_info_categories": [
        "functional_requirements",
        "non_functional_requirements",
        "technical_architecture",
        "technology_stack",
        "testing_strategy",
        "user_workflows"
    ],
    
    # Coverage thresholds
    "coverage_thresholds": {
        "high": 0.8,    # 80%+ coverage = high readiness
        "medium": 0.5,  # 50-80% coverage = medium readiness
        "low": 0.0      # <50% coverage = low readiness
    }
}

# Processing Settings
PROCESSING_CONFIG = {
    # Enable parallel processing for multiple documents
    "enable_parallel_processing": False,
    
    # Verbose logging
    "verbose": True,
    
    # Save intermediate results
    "save_intermediate_results": True,
    
    # Intermediate results directory
    "intermediate_dir": "outputs/intermediate"
}
