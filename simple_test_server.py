#!/usr/bin/env python3
"""
Super Simple Test Server
"""

print("🔄 Starting simple test server...")

try:
    import http.server
    import socketserver
    import os
    from pathlib import Path
    
    # Change to static directory
    static_dir = Path("src/static")
    if static_dir.exists():
        os.chdir(static_dir)
        print(f"✅ Changed to directory: {static_dir.absolute()}")
    else:
        print(f"❌ Static directory not found: {static_dir}")
        exit(1)
    
    PORT = 8000
    
    class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🚀 Server running at http://localhost:{PORT}")
        print(f"📊 Dashboard: http://localhost:{PORT}/index.html")
        print("Press Ctrl+C to stop")
        httpd.serve_forever()
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
