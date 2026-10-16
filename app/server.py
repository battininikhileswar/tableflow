from __future__ import annotations
import base64, json, mimetypes, os, re, shutil, threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import fitz
from PIL import Image, ImageOps
from .ai_config import get_settings,public_settings,update_settings
from .ai_agent import extract_ai,revalidate
from .accounts import Accounts
from .engine import MAX_BYTES, extract, validate, export_xlsx, export_pdf, suggest_headers, FITZ_LOCK

ROOT=Path(__file__).resolve().parents[1]
default_data = '/tmp/tableflow_data' if os.getenv('VERCEL') else str(ROOT/'data')
DATA=Path(os.getenv('TABLEFLOW_DATA',default_data)).resolve()
DATA.mkdir(parents=True,exist_ok=True)
ACCOUNTS=Accounts(DATA)
ATTEMPTS={}
LOCK=threading.RLock(); POOL=ThreadPoolExecutor(max_workers=1)
JOBS={}
for p in DATA.glob('*/job.json'):
    try:
        job=json.loads(p.read_text())
        if job['status'] in ('queued','processing'): job.update(status='failed',error='App restarted during processing. Retry this document.')
        JOBS[job['id']]=job
    except (ValueError,KeyError): pass


def save(job):
    with LOCK:
        JOBS[job['id']]=job
        folder=DATA/job['id'];folder.mkdir(exist_ok=True)
        temp=folder/'job.tmp';temp.write_text(json.dumps(job),encoding='utf-8');temp.replace(folder/'job.json')


def run_job(jid,ai_settings=None):
    with LOCK: job=JOBS[jid];job.update(status='processing',message='Inspecting document');save(job)
    try:
        def progress(current,total,message):
            with LOCK: job.update(progress=round(current/total*100),message=message);save(job)
        if job.get('mode')=='ai':
            result=extract_ai(DATA/jid/'source',job['filename'],progress,**(ai_settings or get_settings(job['owner'])))
        else:
            result=extract(DATA/jid/'source',job['filename'],progress,job['language'],job['force_ocr'])
        with LOCK:
            job['message']='Generating workbooks';save(job)
            export_xlsx(result,DATA/jid/'extracted.xlsx')
            export_pdf(result,DATA/jid/'extracted.pdf')
            job['workbook_ready']=True
        with LOCK: job.update(status='complete',progress=100,message='Excel & PDF ready · review flags included',result=result,error=None);save(job)
    except Exception as exc:
        with LOCK: job.update(status='failed',error=str(exc)[:600],message='Processing stopped');save(job)


def create_job(content,name,language='eng',force=False,owner=None,mode='ai'):
    if not content: raise ValueError('Choose a non-empty document.')
    if len(content)>MAX_BYTES: raise ValueError('Maximum file size is 30 MB.')
    if not re.fullmatch(r'[a-zA-Z_+]{1,50}',language): raise ValueError('Invalid OCR language.')
    if not (content.startswith(b'%PDF-') or content.startswith(b'\x89PNG') or content.startswith(b'\xff\xd8') or content[:4] in (b'II*\x00',b'MM\x00*')):
        raise ValueError('Upload a PDF, PNG, JPEG or single-frame TIFF file.')
    if mode not in ('ai','local'):raise ValueError('Choose AI or local extraction mode.')
    settings=get_settings(owner) if mode=='ai' else None
    if mode=='ai' and not settings['key']:raise ValueError('Configure a Gemini API key in Account settings → AI engine before uploading in AI mode.')
    with LOCK:
        if sum(j['status'] in ('queued','processing') for j in JOBS.values())>=8: raise ValueError('Queue is full. Wait for a document to finish.')
        jid=uuid.uuid4().hex
        folder=DATA/jid;folder.mkdir()
        (folder/'source').write_bytes(content)
        job=dict(id=jid,owner=owner,mode=mode,export_count=0,filename=Path(name.replace('\\','/')).name[:160] or 'document',status='queued',progress=0,message='Waiting for extraction',created=time.time(),language=language,force_ocr=force,error=None)
        save(job)
        if os.getenv('VERCEL') or os.getenv('TABLEFLOW_SYNC'):
            run_job(jid,settings)
        else:
            POOL.submit(run_job,jid,settings)
        return jid


class Handler(BaseHTTPRequestHandler):
    server_version='Tableflow/1.0'
    def log_message(self,*args): pass
    def send(self,code,body,ctype='application/json',headers=None):
        if isinstance(body,(dict,list)): body=json.dumps(body).encode()
        if isinstance(body,str): body=body.encode()
        self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' blob: data:; frame-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers();self.wfile.write(body)
    def body(self,limit=MAX_BYTES):
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError: raise ValueError('Invalid content length.')
        if size<1 or size>limit: raise ValueError(f'Body must be between 1 and {limit} bytes.')
        self.connection.settimeout(45)
        data=self.rfile.read(size)
        if len(data)!=size: raise ValueError('Upload interrupted. Retry the document.')
        return data
    def json_body(self,limit):
        data=json.loads(self.body(limit))
        if not isinstance(data,dict):raise ValueError('Request must be a JSON object.')
        return data
    def safe_origin(self):
        host=self.headers.get('Host','')
        allowed_hosts=('localhost','127.0.0.1','[::1]')
        is_allowed=(
            host.split(':')[0] in allowed_hosts or
            host.endswith('.vercel.app') or
            bool(os.getenv('VERCEL')) or
            bool(os.getenv('TABLEFLOW_ALLOW_ANY_HOST'))
        )
        if not is_allowed: return False
        origin=self.headers.get('Origin')
        return not origin or origin in ('http://'+host,'https://'+host)
    def do_GET(self): self.handle_request('GET')
    def do_POST(self): self.handle_request('POST')
    def do_PUT(self): self.handle_request('PUT')
    def do_DELETE(self): self.handle_request('DELETE')
    def handle_request(self,method):
        try:
            if not self.safe_origin(): return self.send(403,{'error':'Only same-origin local requests are accepted.'})
            parsed=urlparse(self.path);path=parsed.path;q=parse_qs(parsed.query)
            if method=='GET' and path=='/api/health':
                return self.send(200,dict(ok=True,ocr=bool(os.getenv('TESSERACT_CMD') or shutil.which('tesseract')),ai=bool(os.getenv('OPENAI_API_KEY'))))
            user=ACCOUNTS.user_for(self.headers.get('Cookie'))
            if path in ('/api/auth/register','/api/auth/login') and method=='POST':
                now=time.time();ip=self.client_address[0]
                with LOCK:
                    attempts=[t for t in ATTEMPTS.get(ip,[]) if t>now-60]
                    if len(attempts)>=20:return self.send(429,{'error':'Too many sign-in attempts. Try again in a minute.'})
                    ATTEMPTS[ip]=attempts+[now]
                body=self.json_body(10000)
                if not isinstance(body,dict):raise ValueError('Invalid account request.')
                if path.endswith('register'):user=ACCOUNTS.register(body.get('name'),body.get('email'),body.get('password'))
                else:user=ACCOUNTS.login(body.get('email'),body.get('password'))
                token=ACCOUNTS.new_session(user['id'])
                return self.send(200,{'user':user},'application/json',{'Set-Cookie':'tableflow_session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800'})
            if path=='/api/auth/logout' and method=='POST':
                ACCOUNTS.logout(self.headers.get('Cookie'))
                return self.send(200,{'ok':True},headers={'Set-Cookie':'tableflow_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
            if path=='/api/auth/me' and method=='GET':return self.send(200,{'user':user})
            shared=re.fullmatch(r'/share/([A-Za-z0-9_-]{40,60})',path)
            if shared and method=='GET':
                share=ACCOUNTS.resolve_share(shared[1])
                if not share:return self.send(410,'This Excel share has expired or been revoked.','text/plain')
                snapshot=DATA/'shares'/(share['id']+'.xlsx')
                if not snapshot.is_file():return self.send(410,'This Excel share is no longer available.','text/plain')
                return self.send(200,snapshot.read_bytes(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',{'Content-Disposition':'attachment; filename="shared-tableflow.xlsx"','Referrer-Policy':'no-referrer'})
            protected=path.startswith('/api/jobs') or path in ('/api/plan','/api/shares','/api/ai/settings') or path.startswith('/api/shares/')
            if protected and not user:return self.send(401,{'error':'Sign in to your workspace first.'})
            if path=='/api/ai/settings' and method=='GET':return self.send(200,public_settings(user['id']))
            if path=='/api/ai/settings' and method=='PUT':return self.send(200,update_settings(user['id'],self.json_body(2000)))
            if path=='/api/plan' and method=='PUT':
                body=self.json_body(1000);return self.send(200,{'user':ACCOUNTS.set_plan(user['id'],body.get('plan'))})
            if path=='/api/shares' and method=='GET':return self.send(200,ACCOUNTS.shares(user['id']))
            revoke=re.fullmatch(r'/api/shares/([a-f0-9]{32})',path)
            if revoke and method=='DELETE':
                ACCOUNTS.revoke(user['id'],revoke[1]);snapshot=DATA/'shares'/(revoke[1]+'.xlsx')
                # Only remove snapshots owned by this account.
                if any(x['id']==revoke[1] for x in ACCOUNTS.shares(user['id'])):snapshot.unlink(missing_ok=True)
                return self.send(200,{'revoked':True})
            if method=='GET' and path=='/api/jobs':
                with LOCK: data=[{k:v for k,v in j.items() if k!='result'} | {'summary':{'pages':j.get('result',{}).get('page_count',0),'rows':sum(len(t['rows']) for t in j.get('result',{}).get('tables',[])),'flags':len(j.get('result',{}).get('issues',[]))}} for j in sorted(JOBS.values(),key=lambda j:j['created'],reverse=True) if j.get('owner')==user['id']]
                return self.send(200,data)
            if method=='GET' and path.startswith('/samples/'):
                f=ROOT/'samples'/Path(path).name
                if not f.is_file() or f.suffix not in ('.pdf','.png','.xlsx'): return self.send(404,{'error':'Sample not found.'})
                return self.send(200,f.read_bytes(),mimetypes.guess_type(f.name)[0] or 'application/octet-stream')
            if method=='POST' and path=='/api/jobs':
                jid=create_job(self.body(),q.get('name',['document.pdf'])[0],q.get('language',['eng'])[0],q.get('ocr',['0'])[0]=='1',user['id'],q.get('mode',['ai'])[0])
                return self.send(202,{'id':jid})
            match=re.fullmatch(r'/api/jobs/([a-f0-9]{32})(?:/(.*))?',path)
            if match:
                jid,action=match.groups()
                with LOCK: job=JOBS.get(jid)
                if not job or job.get('owner')!=user['id']: return self.send(404,{'error':'Document not found.'})
                if method=='GET' and not action:
                    with LOCK: return self.send(200,job)
                if method=='POST' and action=='retry':
                    new=create_job((DATA/jid/'source').read_bytes(),job['filename'],job['language'],job['force_ocr'],user['id'],job.get('mode','local'))
                    return self.send(202,{'id':new})
                if method=='DELETE' and not action:
                    with LOCK:
                        if job['status'] in ('processing','queued'): return self.send(409,{'error':'Wait for processing to finish before deleting.'})
                        for share in ACCOUNTS.shares(user['id']):
                            if share['job_id']==jid:
                                ACCOUNTS.revoke(user['id'],share['id']);(DATA/'shares'/(share['id']+'.xlsx')).unlink(missing_ok=True)
                        shutil.rmtree(DATA/jid);del JOBS[jid]
                    return self.send(200,{'deleted':True})
                if job['status']!='complete': return self.send(409,{'error':'Document is not ready yet.'})
                if method=='PUT' and action=='tables':
                    data=self.json_body(8_000_000);incoming=data.get('tables')
                    with LOCK:
                        original=job['result']['tables']
                        if not isinstance(incoming,list) or len(incoming)!=len(original): raise ValueError('Invalid table count.')
                        updated=[]
                        for old,new in zip(original,incoming):
                            if not isinstance(new,dict) or new.get('id')!=old['id']: raise ValueError('Invalid table ID.')
                            headers=new.get('headers');rows=new.get('rows')
                            if not isinstance(headers,list) or len(headers)!=len(old['headers']) or not all(isinstance(h,str) and 0<len(h)<=200 for h in headers): raise ValueError('Headers must be non-empty text, at most 200 characters.')
                            if not isinstance(rows,list) or len(rows)!=len(old['rows']): raise ValueError('Row count changed. Reload the document.')
                            if any(not isinstance(r,list) or len(r)!=len(headers) or any(not isinstance(v,str) or len(v)>4000 for v in r) for r in rows): raise ValueError('Invalid cells. Maximum 4,000 characters each.')
                            updated.append({**old,'headers':headers,'rows':rows})
                        job['result']['tables']=updated;job['result']['issues']=revalidate(job['result']);job['edited_at']=time.time();save(job)
                        export_xlsx(job['result'],DATA/jid/'extracted.xlsx');export_pdf(job['result'],DATA/jid/'extracted.pdf')
                    return self.send(200,job)
                if method=='POST' and action=='share':
                    body=self.json_body(1000);hours=body.get('hours',24)
                    if hours not in (1,24,168):raise ValueError('Choose a valid expiry.')
                    with LOCK:
                        folder=DATA/'shares';folder.mkdir(exist_ok=True)
                        # Export first so invalid documents cannot leave a usable share token.
                        target=folder/(uuid.uuid4().hex+'.tmp');export_xlsx(job['result'],target)
                        share=ACCOUNTS.create_share(user['id'],jid,hours);target.replace(folder/(share['id']+'.xlsx'))
                    return self.send(201,{'id':share['id'],'path':'/share/'+share['token'],'expires':share['expires']})
                if method=='POST' and action=='suggest':
                    data=self.json_body(10000);t=next((t for t in job['result']['tables'] if t['id']==data.get('table')),None)
                    if not t: raise ValueError('Choose a table first.')
                    return self.send(200,{'headers':suggest_headers(t)})
                if method=='GET' and action=='report': return self.send(200,job['result'],headers={'Content-Disposition':'attachment; filename="validation-report.json"'})
                if method=='GET' and action=='export':
                    with LOCK:
                        target=DATA/jid/'extracted.xlsx';export_xlsx(job['result'],target)
                        content=target.read_bytes();job['export_count']=job.get('export_count',0)+1;save(job)
                    return self.send(200,content,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',{'Content-Disposition':'attachment; filename="tableflow-extracted.xlsx"'})
                if method=='GET' and action=='export-pdf':
                    with LOCK:
                        target=DATA/jid/'extracted.pdf'
                        if not target.exists(): export_pdf(job['result'],target)
                        content=target.read_bytes();job['export_count']=job.get('export_count',0)+1;save(job)
                    return self.send(200,content,'application/pdf',{'Content-Disposition':'attachment; filename="tableflow-extracted.pdf"'})
                if method=='GET' and action=='source':
                    original=(DATA/jid/'source').read_bytes()
                    suffix='.pdf' if original.startswith(b'%PDF-') else '.png' if original.startswith(b'\x89PNG') else '.jpg' if original.startswith(b'\xff\xd8') else '.tiff'
                    return self.send(200,original,'application/octet-stream',{'Content-Disposition':'attachment; filename="original-source'+suffix+'"'})
                preview=re.fullmatch(r'page/(\d+)\.png',action or '')
                if method=='GET' and preview:
                    page=int(preview[1]);source=DATA/jid/'source'
                    if not 1<=page<=job['result']['page_count']: raise ValueError('Invalid page.')
                    if source.read_bytes()[:5]==b'%PDF-':
                        with FITZ_LOCK, fitz.open(source) as doc:
                            p=doc[page-1];scale=min(1.4,(8_000_000/max(1,p.rect.width*p.rect.height))**.5)
                            content=p.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False).tobytes('png')
                    else:
                        import io
                        with Image.open(source) as image:
                            image=ImageOps.exif_transpose(image);image.thumbnail((1800,1800));buf=io.BytesIO();image.convert('RGB').save(buf,format='PNG');content=buf.getvalue()
                    return self.send(200,content,'image/png')
            if path.startswith('/api/'): return self.send(404,{'error':'Endpoint not found.'})
            if method=='GET':
                allowed={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/product.js':'product.js','/product.css':'product.css'}
                if path in allowed:
                    f=ROOT/'web'/allowed[path]
                    return self.send(200,f.read_bytes(),mimetypes.guess_type(f.name)[0] or 'text/plain')
            return self.send(404,{'error':'Not found.'})
        except (ValueError,json.JSONDecodeError) as exc: self.send(400,{'error':str(exc)[:600]})
        except Exception as exc:
            print('Request error:',type(exc).__name__,str(exc)[:200])
            try: self.send(500,{'error':'Request could not be completed. Retry or check the server terminal.'})
            except (BrokenPipeError,ConnectionResetError): pass


def main():
    port=int(os.getenv('PORT','8000'))
    server=ThreadingHTTPServer((os.getenv('TABLEFLOW_HOST','127.0.0.1'),port),Handler)
    print(f'\n  TABLEFLOW / Document intelligence\n  Open http://127.0.0.1:{port}\n  Press Ctrl+C to stop.\n')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close();POOL.shutdown(wait=True)

if __name__=='__main__': main()
