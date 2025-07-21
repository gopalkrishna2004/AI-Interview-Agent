#!/usr/bin/env python3
"""
Simple script to run the Streamlit Interview Agent app
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'langchain_google_genai',
        'langgraph',
        'pymupdf4llm'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install them using:")
        print("   pip install -r requirements.txt")
        return False
    
    return True

def run_streamlit():
    """Run the Streamlit app"""
    print("🚀 Starting AI Interview Agent...")
    print("📱 The app will open in your default browser")
    print("🔗 If it doesn't open automatically, go to: http://localhost:8501")
    print("\n" + "="*50)
    
    try:
        # Run streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down the app...")
    except Exception as e:
        print(f"❌ Error running the app: {e}")

if __name__ == "__main__":
    print("🤖 AI Interview Agent - Streamlit Runner")
    print("="*40)
    
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if check_dependencies():
        print("✅ All dependencies found!")
        run_streamlit()
    else:
        print("\n⚠️  Please install the missing dependencies first.")
        sys.exit(1) 