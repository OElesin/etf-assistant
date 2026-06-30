#!/usr/bin/env python3
"""
Local API startup script for AmpliFolio
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the AmpliFolio API locally"""
    
    print("🚀 Starting AmpliFolio API locally...")
    print("=" * 50)
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/redoc")
    print("=" * 50)
    print()
    print("💡 Test endpoints:")
    print("• GET  /api/v1/etf-data/status")
    print("• GET  /api/v1/etf-data/search?domicile=Ireland")
    print("• POST /api/v1/analyze-investment")
    print("• POST /api/v1/optimize-portfolio")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Set environment for local development
    os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
    os.environ['ENVIRONMENT'] = 'local'
    
    # Start the server
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

if __name__ == "__main__":
    main()