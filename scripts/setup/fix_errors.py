"""
Automated Error Fix Script

Automatically fixes common setup issues:
1. Installs missing dependencies
2. Creates required folders
3. Verifies Qdrant is running
4. Checks environment configuration

Usage:
    python fix_errors.py
"""

import subprocess
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)


def fix_dependencies():
    """Install missing dependencies."""
    print_header("Fixing Dependencies")
    
    print("Installing Python packages from requirements.txt...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("\n💡 Try manually:")
        print("   pip install -r requirements.txt")
        return False


def fix_folders():
    """Create required folders."""
    print_header("Fixing Folder Structure")
    
    required_folders = [
        "parsed_documents",
        "embedding_cache",
        "embedding_cache/metadata",
        "vector_store",
        "logs"
    ]
    
    created = []
    for folder in required_folders:
        path = Path(folder)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(folder)
            print(f"✅ Created: {folder}/")
        else:
            print(f"  Already exists: {folder}/")
    
    if created:
        print(f"\n✅ Created {len(created)} folders")
    else:
        print("\n✅ All folders already exist")
    
    return True


def check_qdrant():
    """Check if Qdrant is running."""
    print_header("Checking Qdrant")
    
    try:
        import requests
        response = requests.get("http://localhost:6333/healthz", timeout=3)
        
        if response.status_code == 200:
            print("✅ Qdrant is running")
            return True
        else:
            print("❌ Qdrant returned error")
            return False
            
    except ImportError:
        print("⚠️  'requests' not installed, skipping check")
        return None
    except Exception:
        print("❌ Qdrant is not running")
        print("\n💡 Start Qdrant:")
        print("   docker-compose up -d qdrant")
        print("\n   Or check if Docker is running:")
        print("   docker ps")
        return False


def check_env():
    """Check environment configuration."""
    print_header("Checking Environment")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found")
        print("\n💡 Create .env file:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your API keys:")
        print("      OPENAI_API_KEY=your-key-here")
        print("      GOOGLE_API_KEY=your-key-here")
        return False
    
    print("✅ .env file exists")
    
    # Check for API keys
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if openai_key and "your-" not in openai_key.lower():
            print("✅ OPENAI_API_KEY configured")
        else:
            print("❌ OPENAI_API_KEY not configured")
            return False
        
        if google_key and "your-" not in google_key.lower():
            print("✅ GOOGLE_API_KEY configured")
        else:
            print("⚠️  GOOGLE_API_KEY not configured (optional)")
        
        return True
        
    except ImportError:
        print("⚠️  python-dotenv not installed")
        return None


def verify_imports():
    """Verify critical imports work."""
    print_header("Verifying Imports")
    
    imports_to_test = [
        ("pymupdf (fitz)", "import fitz"),
        ("qdrant_client", "from qdrant_client import QdrantClient"),
        ("langchain_qdrant", "from langchain_qdrant import QdrantVectorStore"),
        ("langchain_openai", "from langchain_openai import OpenAIEmbeddings"),
        ("docling", "import docling"),
    ]
    
    all_success = True
    
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name} - {e}")
            all_success = False
    
    if all_success:
        print("\n✅ All critical imports successful")
    else:
        print("\n❌ Some imports failed")
        print("\n💡 Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_success


def main():
    """Run all fixes."""
    print_header("Automated Error Fix Script")
    print("This script will fix common setup issues.\n")
    
    results = {}
    
    # Fix dependencies first
    print("Step 1: Installing dependencies...")
    results["dependencies"] = fix_dependencies()
    
    # Create folders
    print("\nStep 2: Creating folders...")
    results["folders"] = fix_folders()
    
    # Verify imports after installation
    print("\nStep 3: Verifying imports...")
    results["imports"] = verify_imports()
    
    # Check Qdrant
    print("\nStep 4: Checking Qdrant...")
    results["qdrant"] = check_qdrant()
    
    # Check environment
    print("\nStep 5: Checking environment...")
    results["env"] = check_env()
    
    # Summary
    print_header("Fix Summary")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    warnings = sum(1 for v in results.values() if v is None)
    
    for name, result in results.items():
        if result is True:
            status = "✅ FIXED"
        elif result is False:
            status = "❌ NEEDS ATTENTION"
        else:
            status = "⚠️  SKIPPED"
        
        print(f"{status}: {name.upper()}")
    
    print(f"\n{passed} fixed, {failed} need attention, {warnings} skipped")
    
    if failed == 0:
        print("\n🎉 All critical issues resolved!")
        print("\nNext steps:")
        print("1. Run validation: python init_qdrant.py")
        print("2. Run tests: python test_qdrant_migration.py")
        print("3. Start server: python server.py")
        return 0
    else:
        print("\n⚠️  Some issues need manual attention.")
        print("Review the output above and follow the suggestions.")
        print("\nFor detailed help, see: ERROR_FIXES.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())


