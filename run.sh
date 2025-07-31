#!/bin/bash

# iHub Bot Startup Script
echo "🤖 Starting iHub Bot - School Assistant Chatbot"
echo "================================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies."
        echo "🔧 Trying to fix HuggingFace compatibility issues..."
        if [ -f "fix_huggingface.py" ]; then
            python3 fix_huggingface.py
        else
            echo "⚠️  Running manual fix..."
            pip uninstall -y sentence-transformers huggingface_hub transformers
            pip install huggingface_hub==0.19.4 transformers==4.36.2 sentence-transformers==2.6.1
        fi
        echo "📦 Retrying dependency installation..."
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "❌ Still failed. Please run: python3 fix_huggingface.py"
            exit 1
        fi
    fi
else
    echo "⚠️  requirements.txt not found. Make sure you're in the correct directory."
    exit 1
fi

# Check if .env file exists, if not create from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Creating .env file from template..."
        cp .env.example .env
        echo "✅ .env file created. You can edit it to add your OpenAI API key."
    fi
fi

# Create necessary directories
mkdir -p static/css static/js templates

echo "🚀 Starting the application..."
echo "📱 Open your browser and go to: http://localhost:5000"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python app.py