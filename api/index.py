import io
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

# Add project root directory to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Ensure VERCEL environment is flagged
os.environ['VERCEL'] = '1'

from app.server import Handler

class CaseInsensitiveDict(dict):
    def __getitem__(self, key):
        for k, v in self.items():
            if k.lower() == str(key).lower(): return v
        raise KeyError(key)
    def get(self, key, default=None):
        for k, v in self.items():
            if k.lower() == str(key).lower(): return v
        return default
    def __contains__(self, key):
        return any(k.lower() == str(key).lower() for k in self.keys())

class WSGIHandler(Handler):
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.body_out = b''
        
        # Build headers dictionary from WSGI environment
        self.headers = CaseInsensitiveDict()
        for k, v in environ.items():
            if k.startswith('HTTP_'):
                h_name = k[5:].replace('_', '-').title()
                self.headers[h_name] = v
            elif k in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                h_name = k.replace('_', '-').title()
                self.headers[h_name] = v
        if 'HTTP_COOKIE' in environ:
            self.headers['Cookie'] = environ['HTTP_COOKIE']
        if 'HTTP_HOST' in environ:
            self.headers['Host'] = environ['HTTP_HOST']
        if 'HTTP_ORIGIN' in environ:
            self.headers['Origin'] = environ['HTTP_ORIGIN']
            
        qs = environ.get('QUERY_STRING', '')
        req_path = None
        if '__path=' in qs:
            from urllib.parse import parse_qs
            p_qs = parse_qs(qs)
            if '__path' in p_qs:
                req_path = p_qs['__path'][0]
                clean_parts = [p for p in qs.split('&') if not p.startswith('__path=')]
                qs = '&'.join(clean_parts)
                
        if not req_path:
            raw_path = environ.get('PATH_INFO', '/')
            if raw_path.startswith('/api/index.py') or raw_path in ('/api', '/api/'):
                raw_path = environ.get('REQUEST_URI') or environ.get('RAW_URI') or raw_path
            req_path = raw_path
            
        parsed = urlparse(req_path)
        self.path = parsed.path or '/'
        if qs:
            self.path += '?' + qs
            
        self.client_address = (environ.get('REMOTE_ADDR', '127.0.0.1'), 0)
        self.rfile = environ.get('wsgi.input', io.BytesIO())
        self.connection = None

    def send(self, code, body, ctype='application/json', headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.body_out = body
        
        status_map = {
            200: 'OK', 201: 'Created', 202: 'Accepted',
            400: 'Bad Request', 401: 'Unauthorized', 403: 'Forbidden',
            404: 'Not Found', 409: 'Conflict', 410: 'Gone',
            429: 'Too Many Requests', 500: 'Internal Server Error'
        }
        status_text = status_map.get(code, 'OK')
        
        resp_headers = [('Content-Type', ctype), ('Content-Length', str(len(body)))]
        for k, v in (headers or {}).items():
            resp_headers.append((str(k), str(v)))
            
        self.start_response(f'{code} {status_text}', resp_headers)

def app(environ, start_response):
    h = WSGIHandler(environ, start_response)
    method = environ.get('REQUEST_METHOD', 'GET')
    h._dispatch(method)
    return [h.body_out]

# Expose aliases for all serverless entrypoint discovery patterns
application = app
handler = app
