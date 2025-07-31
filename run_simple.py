#!/usr/bin/env python3
"""
Simple iHub Bot Startup Script

This script starts the chatbot with minimal dependencies for testing,
bypassing potential ML library issues.
"""

import os
import sys
import warnings

# Suppress common warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def start_simple_mode():
    """Start the app in simple mode with fallback responses only"""
    print("🚀 Starting iHub Bot in Simple Mode")
    print("=" * 40)
    
    # Set environment variables to disable AI features temporarily
    os.environ['AI_PROVIDER'] = 'fallback'
    os.environ['DISABLE_EMBEDDINGS'] = 'true'
    
    try:
        # Import and start the Flask app
        print("📦 Loading application...")
        from app import app
        
        print("✅ Application loaded successfully!")
        print("🌐 Starting web server...")
        print("📱 Open your browser and go to: http://localhost:5000")
        print("🛠️ Admin dashboard: http://localhost:5000/admin")
        print("⏹️  Press Ctrl+C to stop the server")
        print()
        
        # Start the server
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Try running the macOS fix script:")
        print("  python3 fix_macos.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_simple_mode()