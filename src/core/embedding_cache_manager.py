"""
Embedding Cache Manager

Global cache to prevent re-embedding duplicate documents.
Uses SHA256 file hashing for duplicate detection.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from threading import Lock

logger = logging.getLogger(__name__)


class EmbeddingCacheManager:
    """
    Manages global embedding cache to prevent re-embedding duplicate documents.
    
    Cache is shared across all sessions and persists across restarts.
    Uses SHA256 file hashing for duplicate detection.
    """
    
    def __init__(self, cache_dir: str = "embedding_cache"):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = Path(cache_dir)
        self.cache_index_path = self.cache_dir / "index.json"
        self.metadata_dir = self.cache_dir / "metadata"
        
        # Thread safety for cache operations
        self._lock = Lock()
        
        # Ensure directories exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize cache
        self.cache_data = self._load_cache()
        
        logger.info(
            f"EmbeddingCacheManager initialized: "
            f"cache_dir={cache_dir}, cached_documents={len(self.cache_data['document_hashes'])}"
        )
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache index from disk or create new."""
        if self.cache_index_path.exists():
            try:
                with open(self.cache_index_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                logger.info(f"Loaded cache with {len(cache_data.get('document_hashes', {}))} documents")
                return cache_data
            except Exception as e:
                logger.error(f"Failed to load cache: {e}. Creating new cache.")
        
        # Create new cache structure
        return {
            "document_hashes": {},
            "cache_stats": {
                "total_documents_cached": 0,
                "total_cache_hits": 0,
                "total_cache_misses": 0,
                "cache_hit_rate": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    def _save_cache(self):
        """Save cache index to disk."""
        try:
            with self._lock:
                with open(self.cache_index_path, 'w', encoding='utf-8') as f:
                    json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
                logger.debug("Cache saved successfully")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash string
        """
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # Read file in chunks for memory efficiency
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            file_hash = sha256_hash.hexdigest()
            logger.debug(f"Calculated hash for {Path(file_path).name}: {file_hash[:16]}...")
            return file_hash
            
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            raise
    
    def check_cache(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check if a document with this hash is cached.
        
        Args:
            file_hash: SHA256 hash of the file
            
        Returns:
            Cached metadata if found, None otherwise
        """
        with self._lock:
            if file_hash in self.cache_data["document_hashes"]:
                cached_entry = self.cache_data["document_hashes"][file_hash]
                
                # Update access statistics
                cached_entry["last_accessed"] = datetime.now().isoformat()
                cached_entry["times_reused"] = cached_entry.get("times_reused", 0) + 1
                
                # Update global stats
                self.cache_data["cache_stats"]["total_cache_hits"] += 1
                self._update_hit_rate()
                self._save_cache()
                
                logger.info(
                    f"Cache HIT: {cached_entry['original_filename']} "
                    f"(reused {cached_entry['times_reused']} times)"
                )
                
                return cached_entry
            else:
                # Cache miss
                self.cache_data["cache_stats"]["total_cache_misses"] += 1
                self._update_hit_rate()
                self._save_cache()
                
                logger.debug(f"Cache MISS for hash {file_hash[:16]}...")
                return None
    
    def add_to_cache(
        self,
        file_hash: str,
        metadata: Dict[str, Any]
    ):
        """
        Add a document to the cache.
        
        Args:
            file_hash: SHA256 hash of the file
            metadata: Document metadata including:
                - original_filename
                - file_size_bytes
                - parsed_md_path
                - qdrant_collection
                - qdrant_point_ids
                - chunk_count
                - embedding_model
                - sessions_used_in (optional)
        """
        with self._lock:
            # Prepare cache entry
            cache_entry = {
                "original_filename": metadata.get("original_filename"),
                "file_size_bytes": metadata.get("file_size_bytes"),
                "first_seen": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "times_reused": 0,
                "sessions_used_in": metadata.get("sessions_used_in", []),
                "parsed_md_path": metadata.get("parsed_md_path"),
                "qdrant_collection": metadata.get("qdrant_collection"),
                "qdrant_point_ids": metadata.get("qdrant_point_ids", []),
                "chunk_count": metadata.get("chunk_count", 0),
                "embedding_model": metadata.get("embedding_model"),
                "embedded_at": datetime.now().isoformat()
            }
            
            # Add to cache
            self.cache_data["document_hashes"][file_hash] = cache_entry
            self.cache_data["cache_stats"]["total_documents_cached"] = len(
                self.cache_data["document_hashes"]
            )
            self.cache_data["cache_stats"]["last_updated"] = datetime.now().isoformat()
            
            self._save_cache()
            
            logger.info(
                f"Added to cache: {metadata.get('original_filename')} "
                f"({metadata.get('chunk_count')} chunks)"
            )
    
    def update_session_usage(self, file_hash: str, session_id: str):
        """
        Update which sessions have used this cached document.
        
        Args:
            file_hash: SHA256 hash of the file
            session_id: Session ID using this document
        """
        with self._lock:
            if file_hash in self.cache_data["document_hashes"]:
                entry = self.cache_data["document_hashes"][file_hash]
                sessions = entry.get("sessions_used_in", [])
                
                if session_id not in sessions:
                    sessions.append(session_id)
                    entry["sessions_used_in"] = sessions
                    self._save_cache()
                    logger.debug(f"Updated session usage for hash {file_hash[:16]}...")
    
    def _update_hit_rate(self):
        """Update cache hit rate statistic."""
        stats = self.cache_data["cache_stats"]
        total_requests = stats["total_cache_hits"] + stats["total_cache_misses"]
        
        if total_requests > 0:
            stats["cache_hit_rate"] = stats["total_cache_hits"] / total_requests
        else:
            stats["cache_hit_rate"] = 0.0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "total_documents_cached": self.cache_data["cache_stats"]["total_documents_cached"],
                "total_cache_hits": self.cache_data["cache_stats"]["total_cache_hits"],
                "total_cache_misses": self.cache_data["cache_stats"]["total_cache_misses"],
                "cache_hit_rate": self.cache_data["cache_stats"]["cache_hit_rate"],
                "last_updated": self.cache_data["cache_stats"]["last_updated"]
            }
    
    def get_cached_document_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a cached document.
        
        Args:
            file_hash: SHA256 hash of the file
            
        Returns:
            Document metadata if cached, None otherwise
        """
        with self._lock:
            return self.cache_data["document_hashes"].get(file_hash)
    
    def get_all_cached_documents(self) -> List[Dict[str, Any]]:
        """
        Get list of all cached documents.
        
        Returns:
            List of cached document metadata
        """
        with self._lock:
            return list(self.cache_data["document_hashes"].values())
    
    def clear_cache(self):
        """Clear entire cache (use with caution)."""
        with self._lock:
            self.cache_data = {
                "document_hashes": {},
                "cache_stats": {
                    "total_documents_cached": 0,
                    "total_cache_hits": 0,
                    "total_cache_misses": 0,
                    "cache_hit_rate": 0.0,
                    "last_updated": datetime.now().isoformat()
                }
            }
            self._save_cache()
            logger.warning("Cache cleared completely")
    
    def remove_from_cache(self, file_hash: str):
        """
        Remove a specific document from cache.
        
        Args:
            file_hash: SHA256 hash of the file to remove
        """
        with self._lock:
            if file_hash in self.cache_data["document_hashes"]:
                removed = self.cache_data["document_hashes"].pop(file_hash)
                self.cache_data["cache_stats"]["total_documents_cached"] = len(
                    self.cache_data["document_hashes"]
                )
                self._save_cache()
                logger.info(f"Removed from cache: {removed.get('original_filename')}")
            else:
                logger.warning(f"Hash not found in cache: {file_hash[:16]}...")


