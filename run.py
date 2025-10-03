#!/usr/bin/env python3
"""
Bao Chat Runner Script
Simple script to start the Bao Chat application
"""

import os
import sys
import subprocess

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Check if virtual environment exists
    venv_path = os.path.join(script_dir, 'venv')
    if not os.path.exists(venv_path):
        print("❌ Virtual environment not found!")
        print("Please run setup.sh first or create venv manually:")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate")
        print("  pip install -r requirements.txt")
        sys.exit(1)

    # Get the Python executable from venv
    python_exe = os.path.join(venv_path, 'bin', 'python')
    if not os.path.exists(python_exe):
        print("❌ Python executable not found in virtual environment!")
        sys.exit(1)

    # Check if backend directory exists
    backend_path = os.path.join(script_dir, 'backend')
    if not os.path.exists(backend_path):
        print("❌ Backend directory not found!")
        sys.exit(1)

    print("🥟 Starting Bao Chat...")
    print("📍 Local access: http://localhost:8000")
    print("🌐 Network access: http://[PI_IP]:8000")
    print("🛑 Press Ctrl+C to stop")
    print("")

    try:
        # Start the FastAPI application
        subprocess.run([
            python_exe, '-m', 'uvicorn',
            'backend.app:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload'
        ], cwd=script_dir)
    except KeyboardInterrupt:
        print("\n🛑 Bao Chat stopped. Goodbye! 🥟")
    except Exception as e:
        print(f"❌ Error starting Bao Chat: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()