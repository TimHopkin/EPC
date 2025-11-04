#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "webapp"))

# Set environment
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Import Flask app
try:
    from webapp.app import app
    
    print("🚀 EPC Data Explorer - Full Application")
    print("=" * 50)
    print("📊 Features Available:")
    print("  • Dashboard with live statistics")
    print("  • Advanced search (postcode, UPRN, local authority)")
    print("  • Interactive maps with energy ratings")
    print("  • Analytics charts and insights") 
    print("  • CSV & GeoJSON export")
    print("  • Real-time EPC API data")
    print("=" * 50)
    print("🌐 Access at: http://127.0.0.1:9000")
    print("🔧 Starting server...")
    print()
    
    # Run with different settings
    app.run(
        host='127.0.0.1', 
        port=9000, 
        debug=False,  # Disable debug mode
        use_reloader=False,  # Disable auto-reload
        threaded=True
    )
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import...")
    
    # Alternative import method
    sys.path.append(str(Path(__file__).parent / "webapp"))
    import app as webapp_app
    
    webapp_app.app.run(
        host='127.0.0.1',
        port=9000,
        debug=False,
        use_reloader=False,
        threaded=True
    )