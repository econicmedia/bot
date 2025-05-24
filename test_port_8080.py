#!/usr/bin/env python3
"""
Test Server on Port 8080
"""

print("🔄 Testing server on port 8080...")

try:
    from fastapi import FastAPI, Response
    from fastapi.responses import HTMLResponse
    import uvicorn
    
    app = FastAPI()
    
    @app.get("/", response_class=HTMLResponse)
    def root():
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Trading Bot - Test</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(255,255,255,0.1);
                    padding: 40px;
                    border-radius: 15px;
                }
                .success { color: #4CAF50; font-size: 2em; margin-bottom: 20px; }
                .info { font-size: 1.2em; margin: 20px 0; }
                .button {
                    background: #4CAF50;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 8px;
                    font-size: 1.1em;
                    cursor: pointer;
                    margin: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅ AI Trading Bot Server is WORKING!</div>
                <div class="info">🚀 Server successfully started on port 8080</div>
                <div class="info">📊 This confirms the server can run properly</div>
                <div class="info">🔧 The issue was likely a port conflict on 8000</div>
                <br>
                <button class="button" onclick="window.location.reload()">Refresh</button>
                <button class="button" onclick="testAPI()">Test API</button>
            </div>
            
            <script>
                function testAPI() {
                    fetch('/api/test')
                        .then(response => response.json())
                        .then(data => alert('API Test: ' + data.message))
                        .catch(error => alert('API Error: ' + error));
                }
            </script>
        </body>
        </html>
        """
    
    @app.get("/api/test")
    def test_api():
        return {"status": "success", "message": "API is working perfectly!"}
    
    @app.get("/dashboard")
    def dashboard_redirect():
        return Response(content="Dashboard would be here. Server is working on port 8080!", media_type="text/plain")
    
    print("✅ FastAPI app created successfully")
    print("🚀 Starting server on http://localhost:8080")
    print("📊 Test URL: http://localhost:8080")
    
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="info")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
