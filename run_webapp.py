#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'webapp'))

# Import and run the app
from webapp.app import app

if __name__ == '__main__':
    print("🚀 Starting EPC Data Explorer...")
    print("📍 Access at: http://localhost:8080")
    print("🔧 Debug mode: ON")
    print("🌐 Host: localhost (secure)")
    print("\n" + "="*50)
    
    app.run(
        host='localhost',
        port=8080,
        debug=True,
        threaded=True,
        use_reloader=False
    )