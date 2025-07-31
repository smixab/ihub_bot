#!/usr/bin/env python3
"""
Fix HuggingFace Hub Import Error

This script resolves the 'cached_download' import error by ensuring
compatible versions of huggingface_hub and sentence-transformers are installed.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {cmd}")
            return True
        else:
            print(f"❌ {cmd}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Failed to run {cmd}: {e}")
        return False

def fix_huggingface_issue():
    """Fix the huggingface_hub cached_download import error"""
    print("🔧 Fixing HuggingFace Hub import error...")
    print("=" * 50)
    
    # Step 1: Uninstall problematic packages
    print("\n📦 Step 1: Removing problematic packages...")
    packages_to_remove = [
        "sentence-transformers",
        "huggingface_hub", 
        "transformers"
    ]
    
    for package in packages_to_remove:
        print(f"Removing {package}...")
        run_command(f"pip uninstall -y {package}")
    
    # Step 2: Install compatible versions
    print("\n📦 Step 2: Installing compatible versions...")
    compatible_packages = [
        "huggingface_hub==0.19.4",
        "transformers==4.36.2", 
        "sentence-transformers==2.6.1"
    ]
    
    for package in compatible_packages:
        print(f"Installing {package}...")
        if not run_command(f"pip install {package}"):
            print(f"⚠️ Failed to install {package}")
            return False
    
    # Step 3: Test the fix
    print("\n🧪 Step 3: Testing the fix...")
    try:
        from sentence_transformers import SentenceTransformer
        print("✅ sentence_transformers import successful")
        
        # Test model loading
        print("Testing model loading...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loading successful")
        
        # Test encoding
        print("Testing encoding...")
        embeddings = model.encode(["test sentence"])
        print(f"✅ Encoding successful - shape: {embeddings.shape}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import still failing: {e}")
        return False
    except Exception as e:
        print(f"❌ Other error: {e}")
        return False

def main():
    print("🤖 iHub Bot - HuggingFace Fix Script")
    print("=" * 40)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ Warning: Not in a virtual environment")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Exiting. Please activate your virtual environment first.")
            sys.exit(1)
    
    # Run the fix
    if fix_huggingface_issue():
        print("\n🎉 SUCCESS!")
        print("=" * 30)
        print("The HuggingFace import error has been fixed!")
        print("You can now run the iHub Bot application:")
        print("  python app.py")
        print("or")
        print("  ./run.sh")
        
    else:
        print("\n❌ FAILED!")
        print("=" * 20)
        print("The fix was not successful. Try:")
        print("1. Make sure you're in a virtual environment")
        print("2. Run: pip install --upgrade pip")
        print("3. Run this script again")
        print("4. If still failing, try:")
        print("   pip install --no-cache-dir sentence-transformers==2.6.1")

if __name__ == "__main__":
    main()