#!/usr/bin/env python3
"""
Minimal Server Test
Test basic FastAPI functionality
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_minimal_server():
    """Test minimal FastAPI server"""
    print("🧪 Testing Minimal FastAPI Server")
    print("=" * 40)
    
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        import uvicorn
        
        # Create minimal app
        app = FastAPI(title="Test Server")
        
        @app.get("/")
        async def root():
            return {"message": "Server is working!"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "message": "Minimal server test"}
        
        print("✅ FastAPI app created successfully")
        print("🚀 Starting server on http://localhost:8001...")
        
        # Start server on different port to avoid conflicts
        uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
        
    except Exception as e:
        print(f"❌ Minimal server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_minimal_server()
