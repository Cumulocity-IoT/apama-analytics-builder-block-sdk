# #!/usr/bin/env python
# A python script for mocking HTTP server. It just print all the request received from the client. It does not support HTTPS.
#

import http.server
import socketserver
import sys, json, time

print("Starting")

PORT = int(sys.argv[1])

class RequestHandler(http.server.BaseHTTPRequestHandler):
	def getBody(self):
		"""
		Returns the content of the request body.
		"""
		length = self.headers['Content-Length']
		content = self.rfile.read(int(length))
		return content

	def do_POST(self):
		"""
		Doubles the value.value entry in the JSON, whether it's a number or string.
		"""
		data = json.loads(self.getBody())
		print("Request data: ", data)
		self.send_response(200)
		self.send_header("Content-type", "application/json")
		self.end_headers()
		data['value']['value'] = data['value']['value'] * 2
		self.wfile.write(json.dumps(data).encode('utf-8'))
		sys.stdout.flush()

httpd = socketserver.TCPServer(("", PORT), RequestHandler)

print("serving at port", PORT)
sys.stdout.flush()
httpd.serve_forever()
print("Exiting")
sys.stdout.flush()
