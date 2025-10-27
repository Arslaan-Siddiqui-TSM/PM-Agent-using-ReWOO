"""
Cache Manager

Manages caching of document classifications, extractions, and analysis reports
to optimize performance for repeated operations.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from agents.document_classifier import DocumentClassification
from agents.content_extractor import ExtractedContent
from core.document_analyzer import DocumentAnalysisReport


class CacheManager:
    """
    Manages caching for document intelligence operations.
    
    Caching strategy:
    - Hash PDF files to detect changes
    - Cache classifications per document
    - Cache extractions per document
    - Cache analysis reports per document set
    - Incremental updates when only some documents change
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Subdirectories for different cache types
        self.classification_dir = self.cache_dir / "classifications"
        self.extraction_dir = self.cache_dir / "extractions"
        self.analysis_dir = self.cache_dir / "analysis"
        
        self.classification_dir.mkdir(exist_ok=True)
        self.extraction_dir.mkdir(exist_ok=True)
        self.analysis_dir.mkdir(exist_ok=True)
        
        # Cache index to track file hashes
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load cache index from disk."""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"files": {}, "last_updated": None}
    
    def _save_index(self):
        """Save cache index to disk."""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _get_cache_key(self, filepath: str) -> str:
        """Generate cache key from filepath."""
        return hashlib.md5(filepath.encode()).hexdigest()
    
    def is_file_cached(self, filepath: str) -> bool:
        """Check if file is in cache and unchanged."""
        cache_key = self._get_cache_key(filepath)
        
        if cache_key not in self.index["files"]:
            return False
        
        cached_info = self.index["files"][cache_key]
        current_hash = self._calculate_file_hash(filepath)
        
        return cached_info["hash"] == current_hash
    
    def cache_classification(
        self,
        filepath: str,
        classification: DocumentClassification
    ):
        """Cache a document classification."""
        cache_key = self._get_cache_key(filepath)
        file_hash = self._calculate_file_hash(filepath)
        
        # Save classification to file
        cache_file = self.classification_dir / f"{cache_key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            # Convert dataclass to dict
            from dataclasses import asdict
            json.dump(asdict(classification), f, indent=2)
        
        # Update index
        self.index["files"][cache_key] = {
            "filepath": filepath,
            "hash": file_hash,
            "classification_cached": True,
            "classification_file": str(cache_file),
            "last_classified": datetime.now().isoformat()
        }
        self._save_index()
    
    def get_cached_classification(
        self,
        filepath: str
    ) -> Optional[DocumentClassification]:
        """Retrieve cached classification if available and valid."""
        if not self.is_file_cached(filepath):
            return None
        
        cache_key = self._get_cache_key(filepath)
        cache_info = self.index["files"].get(cache_key, {})
        
        if not cache_info.get("classification_cached"):
            return None
        
        cache_file = cache_info.get("classification_file")
        if not cache_file or not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return DocumentClassification(**data)
        except Exception:
            return None
    
    def cache_extraction(
        self,
        filepath: str,
        extraction: ExtractedContent
    ):
        """Cache extracted content."""
        cache_key = self._get_cache_key(filepath)
        
        # Save extraction to file
        cache_file = self.extraction_dir / f"{cache_key}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            from dataclasses import asdict
            json.dump(asdict(extraction), f, indent=2)
        
        # Update index
        if cache_key not in self.index["files"]:
            self.index["files"][cache_key] = {
                "filepath": filepath,
                "hash": self._calculate_file_hash(filepath)
            }
        
        self.index["files"][cache_key].update({
            "extraction_cached": True,
            "extraction_file": str(cache_file),
            "last_extracted": datetime.now().isoformat()
        })
        self._save_index()
    
    def get_cached_extraction(
        self,
        filepath: str
    ) -> Optional[ExtractedContent]:
        """Retrieve cached extraction if available and valid."""
        if not self.is_file_cached(filepath):
            return None
        
        cache_key = self._get_cache_key(filepath)
        cache_info = self.index["files"].get(cache_key, {})
        
        if not cache_info.get("extraction_cached"):
            return None
        
        cache_file = cache_info.get("extraction_file")
        if not cache_file or not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ExtractedContent(**data)
        except Exception:
            return None
    
    def cache_analysis_report(
        self,
        document_set_id: str,
        report: DocumentAnalysisReport
    ):
        """Cache analysis report for a document set."""
        cache_file = self.analysis_dir / f"{document_set_id}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            from dataclasses import asdict
            json.dump(asdict(report), f, indent=2)
    
    def get_cached_analysis_report(
        self,
        document_set_id: str
    ) -> Optional[DocumentAnalysisReport]:
        """Retrieve cached analysis report."""
        cache_file = self.analysis_dir / f"{document_set_id}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Need to reconstruct nested dataclasses
            from core.document_analyzer import DocumentGapAnalysis, DocumentConflictAnalysis
            
            gaps = DocumentGapAnalysis(**data["gaps"])
            conflicts = DocumentConflictAnalysis(**data["conflicts"])
            
            data["gaps"] = gaps
            data["conflicts"] = conflicts
            
            return DocumentAnalysisReport(**data)
        except Exception:
            return None
    
    def generate_document_set_id(self, filepaths: List[str]) -> str:
        """Generate a unique ID for a set of documents."""
        # Sort filepaths for consistent hashing
        sorted_paths = sorted(filepaths)
        combined = "|".join(sorted_paths)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_files = len(self.index["files"])
        classified = sum(
            1 for info in self.index["files"].values()
            if info.get("classification_cached")
        )
        extracted = sum(
            1 for info in self.index["files"].values()
            if info.get("extraction_cached")
        )
        
        return {
            "total_cached_files": total_files,
            "classified_files": classified,
            "extracted_files": extracted,
            "cache_size_mb": self._calculate_cache_size(),
            "last_updated": self.index.get("last_updated")
        }
    
    def _calculate_cache_size(self) -> float:
        """Calculate total cache size in MB."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.cache_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)  # Convert to MB
    
    def clear_cache(self, keep_index: bool = False):
        """Clear all cache files."""
        import shutil
        
        # Remove cache directories
        for directory in [self.classification_dir, self.extraction_dir, self.analysis_dir]:
            if directory.exists():
                shutil.rmtree(directory)
                directory.mkdir()
        
        # Reset or remove index
        if keep_index:
            self.index = {"files": {}, "last_updated": None}
            self._save_index()
        else:
            if self.index_file.exists():
                self.index_file.unlink()
            self.index = {"files": {}, "last_updated": None}
    
    def remove_file_cache(self, filepath: str):
        """Remove cache for a specific file."""
        cache_key = self._get_cache_key(filepath)
        
        if cache_key in self.index["files"]:
            cache_info = self.index["files"][cache_key]
            
            # Remove classification cache
            if cache_info.get("classification_file"):
                try:
                    os.remove(cache_info["classification_file"])
                except FileNotFoundError:
                    pass
            
            # Remove extraction cache
            if cache_info.get("extraction_file"):
                try:
                    os.remove(cache_info["extraction_file"])
                except FileNotFoundError:
                    pass
            
            # Remove from index
            del self.index["files"][cache_key]
            self._save_index()
    
    def get_stale_entries(self, max_age_days: int = 30) -> List[str]:
        """Get list of cache entries older than specified days."""
        from datetime import timedelta
        
        stale_files = []
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        for cache_key, info in self.index["files"].items():
            last_updated = info.get("last_classified") or info.get("last_extracted")
            if last_updated:
                try:
                    updated_date = datetime.fromisoformat(last_updated)
                    if updated_date < cutoff_date:
                        stale_files.append(info["filepath"])
                except ValueError:
                    continue
        
        return stale_files
    
    def cleanup_stale_cache(self, max_age_days: int = 30):
        """Remove cache entries older than specified days."""
        stale_files = self.get_stale_entries(max_age_days)
        
        for filepath in stale_files:
            self.remove_file_cache(filepath)
        
        return len(stale_files)
