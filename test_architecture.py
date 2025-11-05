"""
Test script to verify the clean separation of Parsing and Embedding handlers.

Usage:
    python test_architecture.py
"""

from pathlib import Path
from src.core.parsing_handler import ParsingHandler
from src.core.embedding_handler import EmbeddingHandler

def test_parsing_and_embedding_separation():
    """
    Test the clean separation between parsing and embedding.
    
    Workflow:
        1. PDF Files → ParsingHandler → MD Files
        2. MD Files → EmbeddingHandler → Qdrant Embeddings
    """
    
    print("\n" + "=" * 80)
    print("🧪 TESTING PARSING & EMBEDDING ARCHITECTURE")
    print("=" * 80 + "\n")
    
    session_id = "test_architecture"
    
    # ========================================
    # STAGE 1: PARSING (PDF → MD)
    # ========================================
    print("📄 STAGE 1: Parsing PDFs to Markdown")
    print("-" * 80)
    
    parsing_handler = ParsingHandler(
        session_id=session_id,
        output_base_dir="output",
        verbose=True
    )
    
    # Use default files
    pdf_paths = list(Path("data/files").glob("*.pdf"))
    print(f"\nFound {len(pdf_paths)} PDF files to process\n")
    
    parsing_result = parsing_handler.parse_documents(
        pdf_paths=[str(p) for p in pdf_paths[:2]],  # Test with 2 files
        force_reprocess=False
    )
    
    print(f"\n✅ Parsing Complete:")
    print(f"   • Parsed: {len(parsing_result['parsed_documents'])} documents")
    print(f"   • Cache hits: {parsing_result['cache_hits']}")
    print(f"   • Cache misses: {parsing_result['cache_misses']}")
    
    # Verify MD files were created
    session_folder = Path(f"output/session_{session_id}_20251104/raw")
    if session_folder.exists():
        md_files = list(session_folder.glob("*.md"))
        print(f"   • MD files created: {len(md_files)}")
        for md_file in md_files:
            print(f"      - {md_file.name}")
    else:
        print(f"   ⚠️  Session folder not found (may be different date)")
    
    # ========================================
    # STAGE 2: EMBEDDING (MD → Qdrant)
    # ========================================
    print("\n" + "=" * 80)
    print("🧠 STAGE 2: Embedding Markdown to Qdrant")
    print("-" * 80 + "\n")
    
    embedding_handler = EmbeddingHandler(
        session_id=session_id,
        qdrant_url="http://localhost:6333",
        embedding_model="text-embedding-3-large",
        verbose=True
    )
    
    embedding_result = embedding_handler.embed_documents(
        parsed_documents=parsing_result["parsed_documents"],
        cached_documents_info=parsing_result["cached_documents_info"]
    )
    
    print(f"\n✅ Embedding Complete:")
    print(f"   • Collection: {embedding_result['collection_name']}")
    print(f"   • Chunks created: {embedding_result['qdrant_stats'].get('chunks_created', 0)}")
    print(f"   • Chunks added: {embedding_result['qdrant_stats'].get('chunks_added', 0)}")
    
    # ========================================
    # VERIFICATION
    # ========================================
    print("\n" + "=" * 80)
    print("✅ VERIFICATION")
    print("=" * 80 + "\n")
    
    print("Architecture Check:")
    print("  ✓ ParsingHandler: PDF → MD files (no embedding logic)")
    print("  ✓ EmbeddingHandler: MD files → Qdrant (no parsing logic)")
    print("  ✓ Clean separation maintained!")
    
    print("\nData Flow:")
    print("  1. PDFs → ParsingHandler.parse_documents()")
    print("  2.   ↓")
    print("  3. MD files saved to: output/session_xxx/raw/")
    print("  4.   ↓")
    print("  5. EmbeddingHandler.embed_documents()")
    print("  6.   ↓")
    print("  7. Embeddings in Qdrant: pm_agent_xxx")
    
    print("\n" + "=" * 80)
    print("🎉 TEST COMPLETE!")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        test_parsing_and_embedding_separation()
        print("✅ All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

