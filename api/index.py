"""
Vercel Serverless Function for Flask Application
This file serves as the entry point for Vercel deployment
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask_app import app

# Vercel Python Runtime requires a handler function
# This function will be called by Vercel for each request
def handler(environ, start_response):
    """Handler for Vercel's serverless environment"""
    return app(environ, start_response)

# For local testing
if __name__ == "__main__":
    app.run(debug=True, port=5001)
