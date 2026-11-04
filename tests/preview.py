from http.server import HTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json,os
root=Path('E:/FPGA_Android_20261101');os.chdir(root/'android/app/src/main/assets')
class Handler(SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path=='/preview':
   page=Path('index.html').read_text(encoding='utf-8');mock='''<script>window.Mobile={send(){},scan(){},disconnect(){},clearQueue(){},sendWithDelay(){},save(){},saveTang(){},demo(){return ''}};window.onerror=(m,s,l)=>fetch('/error',{method:'POST',body:JSON.stringify({m,s,l})});</script>'''
   b=page.replace('<script src="protocol.js">',mock+'<script src="protocol.js">').encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(b)
  else:super().do_GET()
 def do_POST(self):
  text=self.rfile.read(int(self.headers['Content-Length'])).decode();print('UI_ERROR',text,flush=True);self.send_response(204);self.end_headers()
HTTPServer(('127.0.0.1',8767),Handler).serve_forever()
