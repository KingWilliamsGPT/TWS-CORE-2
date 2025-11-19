from http.server import BaseHTTPRequestHandler, HTTPServer

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Server is running!")

        # Print raw GET request
        print("\n=== Raw GET Request ===")
        print(self.raw_requestline)
        print(self.headers)
        print("=======================")

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        raw_request = self.rfile.read(content_length).decode('utf-8')

        self.send_response(200)
        self.end_headers()
        
        self.wfile.write(b"Received POST request.\n")
        self.wfile.write(b"Raw Request:\n")
        self.wfile.write(raw_request.encode('utf-8'))

        # Print raw POST request
        print("\n=== Raw POST Request ===")
        print(self.raw_requestline)
        print(self.headers)
        print(raw_request)
        print("========================")

def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Server is running on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()