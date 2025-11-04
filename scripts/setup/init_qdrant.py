"""
Quick initialization script for Qdrant RAG setup.

Verifies:
- Docker is running
- Qdrant is accessible
- Required folders exist
- Cache is initialized
- Dependencies are installed

Usage:
    python init_qdrant.py
"""

import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def check_docker():
    """Check if Docker is running."""
    print_header("Checking Docker")
    
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ Docker is running")
            return True
        else:
            print("❌ Docker is not running")
            print("   Please start Docker Desktop")
            return False
            
    except FileNotFoundError:
        print("❌ Docker not found")
        print("   Please install Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False


def check_qdrant():
    """Check if Qdrant is running."""
    print_header("Checking Qdrant")
    
    try:
        import requests
        
        response = requests.get("http://localhost:6333/healthz", timeout=3)
        
        if response.status_code == 200:
            print("✅ Qdrant is running")
            data = response.json()
            print(f"   Version: {data.get('version', 'unknown')}")
            return True
        else:
            print("❌ Qdrant returned error")
            return False
            
    except ImportError:
        print("⚠️  'requests' not installed, skipping Qdrant check")
        print("   Install: pip install requests")
        return None
    except Exception:
        print("❌ Qdrant is not running")
        print("\n   Start Qdrant with:")
        print("   docker-compose up -d qdrant")
        print("\n   Or check the logs:")
        print("   docker-compose logs qdrant")
        return False


def check_folders():
    """Check if required folders exist."""
    print_header("Checking Folder Structure")
    
    required_folders = [
        "parsed_documents",
        "embedding_cache",
        "embedding_cache/metadata",
        "vector_store",
        "logs"
    ]
    
    all_exist = True
    
    for folder in required_folders:
        path = Path(folder)
        if path.exists():
            print(f"✅ {folder}/")
        else:
            print(f"❌ {folder}/ (missing)")
            all_exist = False
    
    if not all_exist:
        print("\n   Creating missing folders...")
        for folder in required_folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
        print("   ✅ Folders created")
    
    return True


def check_cache():
    """Check embedding cache initialization."""
    print_header("Checking Embedding Cache")
    
    cache_index = Path("embedding_cache/index.json")
    
    if cache_index.exists():
        try:
            import json
            with open(cache_index, 'r') as f:
                cache_data = json.load(f)
            
            doc_count = len(cache_data.get("document_hashes", {}))
            print(f"✅ Cache initialized with {doc_count} cached documents")
            return True
        except Exception as e:
            print(f"⚠️  Cache file exists but is invalid: {e}")
            return False
    else:
        print("ℹ️  Cache not yet initialized (will be created on first use)")
        return True


def check_dependencies():
    """Check if key dependencies are installed."""
    print_header("Checking Python Dependencies")
    
    required_packages = [
        ("qdrant_client", "Qdrant client"),
        ("langchain_qdrant", "LangChain Qdrant"),
        ("langchain_openai", "LangChain OpenAI"),
        ("docling", "Docling (document parsing)"),
        ("pymupdf", "PyMuPDF"),
    ]
    
    all_installed = True
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {description}")
        except ImportError:
            print(f"❌ {description} (not installed)")
            all_installed = False
    
    if not all_installed:
        print("\n   Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_installed


def check_env():
    """Check environment variables."""
    print_header("Checking Environment Configuration")
    
    import os
    from dotenv import load_dotenv
    
    # Try to load .env
    if Path(".env").exists():
        load_dotenv()
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found")
        print("   Copy .env.example to .env and configure your API keys")
    
    # Check critical variables
    required_vars = [
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f"your-{var.lower().replace('_', '-')}-here":
            print(f"✅ {var} configured")
        else:
            print(f"❌ {var} not configured")
            missing_vars.append(var)
    
    if missing_vars:
        print("\n   Configure these variables in your .env file")
        return False
    
    return True


def print_next_steps():
    """Print next steps for the user."""
    print_header("Next Steps")
    
    print("""
1. If Qdrant is not running:
   docker-compose up -d qdrant

2. Run the test suite:
   python test_qdrant_migration.py

3. Start the API server:
   python server.py

4. Test the upload endpoint:
   curl -X POST "http://localhost:8000/api/upload?use_default_files=true"

5. View Qdrant dashboard:
   http://localhost:6333/dashboard

For more information:
- Docker setup: DOCKER_SETUP.md
- Migration details: QDRANT_MIGRATION_COMPLETE.md
- API documentation: http://localhost:8000/docs
""")


def main():
    """Run all checks."""
    print_header("Qdrant RAG Setup - Initialization Check")
    
    checks = [
        ("Docker", check_docker),
        ("Qdrant", check_qdrant),
        ("Folders", check_folders),
        ("Cache", check_cache),
        ("Dependencies", check_dependencies),
        ("Environment", check_env),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    warnings = sum(1 for _, r in results if r is None)
    
    for name, result in results:
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⚠️  WARN"
        
        print(f"{status}: {name}")
    
    print(f"\n{passed} passed, {failed} failed, {warnings} warnings")
    
    if failed == 0:
        print("\n🎉 All critical checks passed!")
        print_next_steps()
        return 0
    else:
        print("\n⚠️  Some checks failed. Review the output above and fix the issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


