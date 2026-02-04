"""
Render-compatible entry point for Flask Application
This file serves as entry point for Render deployment
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask_app import app

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5001)
