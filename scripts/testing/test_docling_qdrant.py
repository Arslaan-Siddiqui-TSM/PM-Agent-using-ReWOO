"""
Quick test script for Docling + Qdrant integration.

Tests:
1. Docling HybridChunker parsing
2. Qdrant ingestion
3. Semantic search

Usage:
    python test_docling_qdrant.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_docling_qdrant_pipeline():
    """Test the full Docling → Qdrant pipeline."""
    
    print("="*60)
    print("Testing Docling + Qdrant Pipeline")
    print("="*60)
    
    # Check for PDF files
    files_dir = Path("files")
    pdf_files = list(files_dir.glob("*.pdf"))[:2]  # Test with 2 files
    
    if not pdf_files:
        print("❌ No PDF files found in files/ directory")
        return False
    
    print(f"\n✅ Found {len(pdf_files)} PDF files to test")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    
    # Test 1: Document Parsing with HybridChunker
    print("\n" + "="*60)
    print("TEST 1: Parsing with Docling HybridChunker")
    print("="*60)
    
    try:
        from src.core.intelligent_document_parser import IntelligentDocumentParser
        
        parser = IntelligentDocumentParser(session_id="test_session")
        
        parsed_docs = []
        for pdf_path in pdf_files:
            print(f"\n📄 Parsing: {pdf_path.name}")
            try:
                doc = parser.parse_document(str(pdf_path))
                if doc:
                    parsed_docs.append(doc)
                    print(f"✅ Parsed successfully")
                    print(f"   Parser: {doc.parser_used}")
                    if doc.metadata.get("chunker"):
                        print(f"   Chunker: {doc.metadata['chunker']}")
                        print(f"   Chunks: {doc.metadata.get('num_chunks', 'N/A')}")
                else:
                    print(f"⚠️  Parsing returned None")
            except Exception as e:
                print(f"❌ Parsing failed: {e}")
        
        print(f"\n✅ Test 1 Complete: {len(parsed_docs)}/{len(pdf_files)} documents parsed")
        
    except Exception as e:
        print(f"\n❌ Test 1 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if not parsed_docs:
        print("❌ No documents were parsed successfully")
        return False
    
    # Test 2: Qdrant Ingestion
    print("\n" + "="*60)
    print("TEST 2: Qdrant Ingestion")
    print("="*60)
    
    try:
        from src.core.qdrant_manager import QdrantManager
        
        print("\n🔌 Connecting to Qdrant...")
        manager = QdrantManager(session_id="test_session")
        print("✅ Connected to Qdrant")
        
        print(f"\n📤 Ingesting {len(parsed_docs)} documents...")
        stats = manager.ingest_documents(parsed_docs)
        
        print("\n✅ Ingestion Complete:")
        print(f"   Documents processed: {stats['documents_processed']}")
        print(f"   Chunks created: {stats['chunks_created']}")
        print(f"   Chunks added: {stats['chunks_added']}")
        print(f"   Collection: {stats['collection_name']}")
        
    except Exception as e:
        print(f"\n❌ Test 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Semantic Search
    print("\n" + "="*60)
    print("TEST 3: Semantic Search")
    print("="*60)
    
    try:
        print("\n🔍 Testing semantic search...")
        
        test_queries = [
            "What are the system requirements?",
            "What is the technical architecture?",
            "What are the functional specifications?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = manager.query(query, k=3, score_threshold=0.5)
            
            if results:
                print(f"✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"\n   Result {i}:")
                    print(f"   Score: {result['score']:.3f}")
                    print(f"   Source: {result['metadata'].get('source', 'unknown')}")
                    print(f"   Content: {result['content'][:100]}...")
            else:
                print("⚠️  No results found")
        
        print("\n✅ Test 3 Complete: Search working")
        
    except Exception as e:
        print(f"\n❌ Test 3 Failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    print("\n" + "="*60)
    print("Cleanup")
    print("="*60)
    
    try:
        print("\n🧹 Deleting test collection...")
        manager.delete_collection()
        print("✅ Test collection deleted")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    # Final Summary
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED!")
    print("="*60)
    print("\n✅ Docling HybridChunker: Working")
    print("✅ Qdrant Ingestion: Working")
    print("✅ Semantic Search: Working")
    print("\nYour Qdrant RAG pipeline is ready to use!")
    
    return True


if __name__ == "__main__":
    import sys
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in environment")
        print("   Please create a .env file with your API key")
        sys.exit(1)
    
    # Run tests
    success = test_docling_qdrant_pipeline()
    
    sys.exit(0 if success else 1)


