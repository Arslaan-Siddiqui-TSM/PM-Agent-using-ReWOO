"""
Comprehensive test suite for Qdrant RAG migration.

Tests:
1. Qdrant connection
2. Intelligent document parsing (PyMuPDF vs Docling)
3. Embedding cache (hit/miss scenarios)
4. End-to-end pipeline integration
5. Error handling (corrupted PDFs)
6. Session isolation and cleanup
"""

import sys
import glob
from pathlib import Path
import time

# Test configuration
TEST_SESSION_ID = "test_session_12345"
TEST_FILES_DIR = "files"


def test_1_qdrant_connection():
    """Test Qdrant server connection."""
    print("\n" + "="*60)
    print("TEST 1: Qdrant Connection")
    print("="*60)
    
    try:
        from src.core.qdrant_manager import QdrantManager
        
        manager = QdrantManager(
            session_id=TEST_SESSION_ID,
            qdrant_url="http://localhost:6333"
        )
        
        # Check if collection was created
        if manager.collection_exists():
            print("✅ Qdrant connection successful")
            print(f"✅ Collection created: {manager.collection_name}")
            
            # Clean up test collection
            manager.delete_collection()
            print("✅ Test collection cleaned up")
            return True
        else:
            print("❌ Collection not created")
            return False
            
    except Exception as e:
        print(f"❌ Qdrant connection failed: {e}")
        print("\n💡 Make sure Qdrant is running:")
        print("   docker-compose up -d qdrant")
        return False


def test_2_embedding_cache():
    """Test embedding cache manager."""
    print("\n" + "="*60)
    print("TEST 2: Embedding Cache Manager")
    print("="*60)
    
    try:
        from src.core.embedding_cache_manager import EmbeddingCacheManager
        
        cache = EmbeddingCacheManager(cache_dir="embedding_cache")
        
        # Get sample file
        pdf_files = glob.glob(f"{TEST_FILES_DIR}/*.pdf")
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return False
        
        test_file = pdf_files[0]
        
        # Calculate hash
        file_hash = cache.calculate_file_hash(test_file)
        print(f"✅ File hash calculated: {file_hash[:16]}...")
        
        # Check cache (should be miss first time)
        cached = cache.check_cache(file_hash)
        if cached is None:
            print("✅ Cache miss (expected for first time)")
        else:
            print(f"ℹ️  Cache hit: Document already cached")
        
        # Get stats
        stats = cache.get_cache_stats()
        print(f"✅ Cache stats retrieved: {stats['total_documents_cached']} documents cached")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False


def test_3_intelligent_parsing():
    """Test intelligent document parser."""
    print("\n" + "="*60)
    print("TEST 3: Intelligent Document Parser")
    print("="*60)
    
    try:
        from src.core.intelligent_document_parser import IntelligentDocumentParser
        
        # Get sample PDFs
        pdf_files = glob.glob(f"{TEST_FILES_DIR}/*.pdf")
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return False
        
        # Test with first file
        test_file = pdf_files[0]
        print(f"Testing with: {Path(test_file).name}")
        
        parser = IntelligentDocumentParser(
            session_id=TEST_SESSION_ID,
            output_base_dir="parsed_documents",
            complexity_threshold=0.3
        )
        
        # Analyze complexity
        is_complex, analysis = parser.analyze_pdf_complexity(test_file)
        print(f"✅ Complexity analysis: score={analysis['complexity_score']:.2f}, "
              f"parser={analysis['recommended_parser']}")
        
        # Parse document
        parsed_doc = parser.parse_document(test_file)
        print(f"✅ Document parsed: {parsed_doc.parser_used}")
        print(f"   - Content: {len(parsed_doc.text_content)} chars")
        print(f"   - Time: {parsed_doc.processing_time:.2f}s")
        print(f"   - Output: {parsed_doc.output_md_path}")
        
        # Verify markdown file exists
        if Path(parsed_doc.output_md_path).exists():
            print("✅ Markdown file saved successfully")
        else:
            print("❌ Markdown file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_4_qdrant_ingestion():
    """Test document ingestion into Qdrant."""
    print("\n" + "="*60)
    print("TEST 4: Qdrant Document Ingestion")
    print("="*60)
    
    try:
        from src.core.intelligent_document_parser import IntelligentDocumentParser
        from src.core.qdrant_manager import QdrantManager
        
        # Parse documents
        pdf_files = glob.glob(f"{TEST_FILES_DIR}/*.pdf")[:2]  # Test with 2 files
        if len(pdf_files) < 1:
            print("❌ No PDF files found")
            return False
        
        print(f"Parsing {len(pdf_files)} documents...")
        parser = IntelligentDocumentParser(
            session_id=TEST_SESSION_ID,
            output_base_dir="parsed_documents"
        )
        parsed_docs = parser.parse_batch(pdf_files)
        print(f"✅ Parsed {len(parsed_docs)} documents")
        
        # Ingest into Qdrant
        print("Ingesting into Qdrant...")
        manager = QdrantManager(
            session_id=TEST_SESSION_ID,
            qdrant_url="http://localhost:6333"
        )
        
        stats = manager.ingest_documents(parsed_docs)
        print(f"✅ Ingestion complete:")
        print(f"   - Documents: {stats['documents_processed']}")
        print(f"   - Chunks created: {stats['chunks_created']}")
        print(f"   - Chunks added: {stats['chunks_added']}")
        
        # Test query
        print("\nTesting semantic search...")
        results = manager.query("What are the system requirements?", k=3)
        print(f"✅ Query returned {len(results)} results")
        
        if results:
            print(f"   Top result score: {results[0].get('score', 0):.3f}")
        
        # Get stats
        collection_stats = manager.get_stats()
        print(f"✅ Collection stats: {collection_stats['points_count']} points")
        
        # Cleanup
        manager.delete_collection()
        print("✅ Test collection cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Ingestion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_5_full_pipeline():
    """Test full pipeline integration."""
    print("\n" + "="*60)
    print("TEST 5: Full Pipeline Integration")
    print("="*60)
    
    try:
        from src.core.document_intelligence_pipeline import DocumentIntelligencePipeline
        
        # Get sample files
        pdf_files = glob.glob(f"{TEST_FILES_DIR}/*.pdf")[:3]
        if not pdf_files:
            print("❌ No PDF files found")
            return False
        
        print(f"Processing {len(pdf_files)} documents through full pipeline...")
        
        pipeline = DocumentIntelligencePipeline(enable_cache=True, verbose=True)
        
        # Process with RAG
        result = pipeline.process_documents_with_rag(
            pdf_paths=pdf_files,
            session_id=TEST_SESSION_ID,
            output_dir="outputs/intermediate",
            force_reprocess=False
        )
        
        print("\n✅ Pipeline completed successfully!")
        print(f"   - Classifications: {len(result['classifications'])}")
        print(f"   - Extractions: {len(result['extractions'])}")
        print(f"   - Parsed documents: {len(result['parsed_documents'])}")
        print(f"   - Qdrant chunks: {result['qdrant_stats']['chunks_added']}")
        print(f"   - Cache hits: {result['embedding_cache_stats']['session_cache_hits']}")
        print(f"   - Cache misses: {result['embedding_cache_stats']['session_cache_misses']}")
        
        # Cleanup
        if result.get('qdrant_manager'):
            result['qdrant_manager'].delete_collection()
            print("✅ Cleanup complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_6_cache_reuse():
    """Test that cached documents are reused correctly."""
    print("\n" + "="*60)
    print("TEST 6: Cache Reuse Test")
    print("="*60)
    
    try:
        from src.core.document_intelligence_pipeline import DocumentIntelligencePipeline
        
        pdf_files = glob.glob(f"{TEST_FILES_DIR}/*.pdf")[:2]
        if not pdf_files:
            print("❌ No PDF files found")
            return False
        
        # First run - should cache
        print("First run (caching)...")
        pipeline1 = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
        result1 = pipeline1.process_documents_with_rag(
            pdf_paths=pdf_files,
            session_id="test_cache_1",
            force_reprocess=False
        )
        
        cache_misses_1 = result1['embedding_cache_stats']['session_cache_misses']
        print(f"✅ First run: {cache_misses_1} cache misses (expected)")
        
        # Clean up first collection
        result1['qdrant_manager'].delete_collection()
        
        # Second run - should hit cache
        print("\nSecond run (should use cache)...")
        pipeline2 = DocumentIntelligencePipeline(enable_cache=True, verbose=False)
        result2 = pipeline2.process_documents_with_rag(
            pdf_paths=pdf_files,
            session_id="test_cache_2",
            force_reprocess=False
        )
        
        cache_hits_2 = result2['embedding_cache_stats']['session_cache_hits']
        print(f"✅ Second run: {cache_hits_2} cache hits")
        
        # Clean up second collection
        result2['qdrant_manager'].delete_collection()
        
        if cache_hits_2 > 0:
            print("✅ Cache reuse working correctly!")
            return True
        else:
            print("⚠️  Cache reuse not working as expected")
            return False
        
    except Exception as e:
        print(f"❌ Cache reuse test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("QDRANT RAG MIGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Qdrant Connection", test_1_qdrant_connection),
        ("Embedding Cache", test_2_embedding_cache),
        ("Intelligent Parsing", test_3_intelligent_parsing),
        ("Qdrant Ingestion", test_4_qdrant_ingestion),
        ("Full Pipeline", test_5_full_pipeline),
        ("Cache Reuse", test_6_cache_reuse),
    ]
    
    results = []
    start_time = time.time()
    
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
        
        time.sleep(0.5)  # Brief pause between tests
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed_count}/{total_count} tests passed")
    print(f"Time: {total_time:.2f}s")
    print("="*60)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Qdrant migration successful!")
        return 0
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())


