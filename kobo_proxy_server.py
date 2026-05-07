"""
KoboToolbox CORS Proxy Server
This simple server allows your dashboard to fetch data from KoboToolbox
by bypassing CORS restrictions.

HOW TO USE:
1. Open PowerShell in this folder
2. Run: python kobo_proxy_server.py
3. Keep this window open while using the dashboard
4. In your dashboard, the data will be fetched through this proxy
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError
import ssl

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Proxy GET requests to KoboToolbox"""
        try:
            # Parse the request path
            # Expected format: /proxy?url=KOBO_URL&token=TOKEN (token optional)
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if 'url' not in query_params:
                self.send_error(400, 'Missing url parameter')
                return
            
            kobo_url = query_params['url'][0]
            kobo_token = query_params.get('token', [None])[0]
            
            # Detect file type
            is_xlsx = '.xlsx' in kobo_url.lower() or 'data.xlsx' in kobo_url.lower()
            is_csv = '.csv' in kobo_url.lower()
            is_export_settings = 'export-settings' in kobo_url.lower()
            
            # Create request to KoboToolbox
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Set appropriate Accept header based on file type
            if is_xlsx:
                headers['Accept'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream, */*'
            elif is_csv:
                headers['Accept'] = 'text/csv, application/csv, text/plain, */*'
            else:
                headers['Accept'] = 'application/json, */*'
            
            # Only add token if provided and not for public export-settings URLs
            if kobo_token and not is_export_settings:
                headers['Authorization'] = f'Token {kobo_token}'
            
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Make request to KoboToolbox
            req = urllib.request.Request(kobo_url, headers=headers)
            
            try:
                with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
                    data = response.read()
                    
                    # Determine content type
                    if is_xlsx:
                        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    elif is_csv:
                        content_type = 'text/csv'
                    else:
                        content_type = 'application/json'
                    
                    # Send successful response
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', len(data))
                    self.end_headers()
                    self.wfile.write(data)
                    
                    file_size = len(data) / 1024  # KB
                    print(f"✓ Successfully proxied {file_size:.1f} KB from: {kobo_url[:60]}...")
                    
            except HTTPError as e:
                error_msg = {
                    'error': f'KoboToolbox returned HTTP {e.code}',
                    'message': str(e.reason)
                }
                
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(error_msg).encode())
                
                print(f"✗ KoboToolbox error {e.code}: {e.reason}")
                
        except Exception as e:
            error_msg = {
                'error': 'Proxy server error',
                'message': str(e)
            }
            
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(error_msg).encode())
            
            print(f"✗ Proxy error: {e}")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=8765):
    """Start the CORS proxy server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSProxyHandler)
    
    print("=" * 70)
    print("🚀 KoboToolbox CORS Proxy Server Started!")
    print("=" * 70)
    print(f"Server running on: http://localhost:{port}")
    print(f"\nℹ️  Keep this window open while using the dashboard")
    print(f"ℹ️  Press Ctrl+C to stop the server")
    print("=" * 70)
    print("\n📡 Waiting for requests...\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()
