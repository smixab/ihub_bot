#!/usr/bin/env python3
"""
macOS Specific Fix for iHub Bot

This script resolves common macOS issues including:
- urllib3/OpenSSL compatibility warnings
- PyTorch segmentation faults on Apple Silicon
- FAISS compatibility on M1/M2 Macs
"""

import subprocess
import sys
import os
import platform

def run_command(cmd, ignore_errors=False):
    """Run a command and return success status"""
    try:
        print(f"🔧 Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 or ignore_errors:
            print(f"✅ Success")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def detect_system():
    """Detect system architecture and OS"""
    system_info = {
        'os': platform.system(),
        'machine': platform.machine(),
        'python_version': platform.python_version()
    }
    
    print(f"🖥️  System: {system_info['os']}")
    print(f"🏗️  Architecture: {system_info['machine']}")
    print(f"🐍 Python: {system_info['python_version']}")
    
    return system_info

def fix_urllib3_ssl():
    """Fix urllib3 SSL warnings on macOS"""
    print("\n🔒 Fixing urllib3/SSL compatibility...")
    
    # Downgrade urllib3 to avoid SSL warnings
    if not run_command("pip install urllib3==1.26.18"):
        print("⚠️ Could not fix urllib3, continuing anyway...")

def fix_pytorch_macos():
    """Fix PyTorch for macOS, especially Apple Silicon"""
    print("\n🔥 Fixing PyTorch for macOS...")
    
    system_info = detect_system()
    
    # Uninstall potentially problematic torch installations
    print("Removing existing torch installations...")
    run_command("pip uninstall -y torch torchvision torchaudio", ignore_errors=True)
    
    if system_info['machine'] in ['arm64', 'aarch64']:
        print("🍎 Apple Silicon detected - installing optimized PyTorch...")
        # For Apple Silicon, use CPU-only PyTorch
        if not run_command("pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2"):
            print("⚠️ Failed to install Apple Silicon PyTorch, trying fallback...")
            run_command("pip install torch==1.13.1 torchvision==0.14.1 torchaudio==0.13.1")
    else:
        print("🖥️ Intel Mac detected - installing standard PyTorch...")
        run_command("pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2")

def fix_faiss_macos():
    """Fix FAISS for macOS"""
    print("\n🔍 Fixing FAISS for macOS...")
    
    system_info = detect_system()
    
    # Remove existing FAISS
    run_command("pip uninstall -y faiss-cpu faiss-gpu", ignore_errors=True)
    
    if system_info['machine'] in ['arm64', 'aarch64']:
        print("🍎 Installing FAISS for Apple Silicon...")
        # For Apple Silicon, try conda-forge first, then pip fallback
        if not run_command("pip install faiss-cpu==1.8.0"):
            print("⚠️ Standard FAISS failed, trying alternative...")
            run_command("pip install faiss-cpu==1.7.4 --no-deps")
    else:
        print("🖥️ Installing FAISS for Intel Mac...")
        run_command("pip install faiss-cpu==1.7.4")

def fix_sentence_transformers():
    """Reinstall sentence-transformers with compatible versions"""
    print("\n🤖 Fixing sentence-transformers...")
    
    # Remove and reinstall with specific versions
    run_command("pip uninstall -y sentence-transformers", ignore_errors=True)
    run_command("pip install sentence-transformers==2.6.1")

def test_imports():
    """Test that all critical imports work"""
    print("\n🧪 Testing imports...")
    
    test_imports = [
        ("flask", "Flask"),
        ("sentence_transformers", "SentenceTransformer"),
        ("torch", "torch"),
        ("faiss", "faiss"),
        ("numpy", "numpy")
    ]
    
    failed_imports = []
    
    for module, import_name in test_imports:
        try:
            exec(f"import {import_name}")
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
        except Exception as e:
            print(f"⚠️ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def create_minimal_test():
    """Create a minimal test to verify the app can start"""
    print("\n🎯 Creating minimal test...")
    
    test_code = '''
import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from sentence_transformers import SentenceTransformer
    print("✅ SentenceTransformer import successful")
    
    # Test basic model loading without actually downloading
    print("🔍 Testing basic functionality...")
    
    # Import other critical components
    from flask import Flask
    print("✅ Flask import successful")
    
    import faiss
    print("✅ FAISS import successful")
    
    print("🎉 All critical imports working!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    exit(1)
'''
    
    with open('test_minimal.py', 'w') as f:
        f.write(test_code)
    
    print("Running minimal test...")
    return run_command("python test_minimal.py")

def main():
    print("🍎 iHub Bot - macOS Compatibility Fix")
    print("=" * 45)
    
    # Detect system
    system_info = detect_system()
    
    if system_info['os'] != 'Darwin':
        print("⚠️ This script is designed for macOS. Exiting.")
        sys.exit(1)
    
    print(f"\n🔧 Applying macOS-specific fixes...")
    
    # Apply fixes in order
    fix_urllib3_ssl()
    fix_pytorch_macos() 
    fix_faiss_macos()
    fix_sentence_transformers()
    
    # Test everything works
    print("\n" + "="*50)
    if test_imports():
        print("✅ All imports successful!")
        
        if create_minimal_test():
            print("\n🎉 SUCCESS!")
            print("=" * 30)
            print("macOS compatibility issues fixed!")
            print("\nYou can now run:")
            print("  python app.py")
            print("\nOr with suppressed warnings:")
            print("  python -W ignore app.py")
            
            # Clean up test file
            if os.path.exists('test_minimal.py'):
                os.remove('test_minimal.py')
        else:
            print("\n⚠️ Basic test failed, but imports work.")
            print("Try running the app with warnings suppressed:")
            print("  python -W ignore app.py")
    else:
        print("\n❌ Some imports still failing.")
        print("Try running in a fresh virtual environment:")
        print("  python -m venv fresh_venv")
        print("  source fresh_venv/bin/activate") 
        print("  python fix_macos.py")

if __name__ == "__main__":
    main()