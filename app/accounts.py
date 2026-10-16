"""Local account/session and revocable sharing storage; no external identity service."""
import base64,hashlib,hmac,json,os,re,secrets,sqlite3,time
from contextlib import contextmanager
from pathlib import Path
from http.cookies import SimpleCookie, CookieError

SIGN_SECRET = (
    os.getenv('TABLEFLOW_SECRET') or 
    os.getenv('GEMINI_API_KEY') or 
    os.getenv('VERCEL_DEPLOYMENT_ID') or 
    'tableflow-stable-session-sign-2026'
).encode('utf-8')
REVOKED = set()

class Accounts:
    def __init__(self,folder):
        self.path=Path(folder)/'accounts.sqlite3'
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,password TEXT NOT NULL,plan TEXT NOT NULL DEFAULT 'starter',created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY,user_id TEXT NOT NULL,expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS shares(id TEXT PRIMARY KEY,digest TEXT UNIQUE NOT NULL,user_id TEXT NOT NULL,job_id TEXT NOT NULL,expires REAL NOT NULL,created REAL NOT NULL,revoked INTEGER NOT NULL DEFAULT 0);
            ''')
    @contextmanager
    def db(self):
        conn=sqlite3.connect(self.path,timeout=15);conn.row_factory=sqlite3.Row
        try:yield conn;conn.commit()
        finally:conn.close()
    def public(self,row):return {k:row[k] for k in ('id','name','email','plan','created')}
    @staticmethod
    def digest(token):return hashlib.sha256(token.encode()).hexdigest()
    @staticmethod
    def password_hash(password,salt=None):
        salt=salt or secrets.token_hex(16)
        return salt+':'+hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1,dklen=32).hex()
    def register(self,name,email,password):
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError('Enter a name between 1 and 80 characters.')
        if not isinstance(email,str) or not re.fullmatch(r'[^\s@]{1,100}@[^\s@]{1,100}\.[^\s@]{2,40}',email):raise ValueError('Enter a valid email address.')
        if not isinstance(password,str) or not 8<=len(password)<=128:raise ValueError('Use a password between 8 and 128 characters.')
        uid=secrets.token_hex(16)
        with self.db() as db:
            try:db.execute('INSERT INTO users(id,email,name,password,created) VALUES(?,?,?,?,?)',(uid,email.strip().lower(),name.strip(),self.password_hash(password),time.time()))
            except sqlite3.IntegrityError:raise ValueError('An account already uses this email. Sign in instead.')
            row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        return self.public(row)
    def login(self,email,password):
        if not isinstance(email,str) or not isinstance(password,str) or len(password)>128:raise ValueError('Email or password is incorrect.')
        with self.db() as db:row=db.execute('SELECT * FROM users WHERE email=?',(email.strip().lower(),)).fetchone()
        expected=row['password'] if row else self.password_hash('unavailable-account')
        actual=self.password_hash(password,expected.split(':')[0])
        if not row or not hmac.compare_digest(actual,expected):raise ValueError('Email or password is incorrect.')
        return self.public(row)
    def new_session(self,uid):
        with self.db() as db:
            row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
            user_data=dict(row) if row else {'id':uid,'name':'User','email':'user@tableflow.app','plan':'starter','created':time.time()}
        expires=time.time()+604800
        payload={'id':user_data['id'],'name':user_data['name'],'email':user_data['email'],'plan':user_data['plan'],'created':user_data['created'],'exp':expires,'n':secrets.token_hex(8)}
        b64=base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig=hmac.new(SIGN_SECRET,b64.encode(),hashlib.sha256).hexdigest()
        token=f"{b64}.{sig}"
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES(?,?,?)',(self.digest(token),uid,expires))
        return token
    def user_for(self,cookie):
        try:c=SimpleCookie();c.load(cookie or '');token=c['tableflow_session'].value
        except (KeyError,ValueError,CookieError):return None
        digest=self.digest(token)
        if digest in REVOKED:return None
        if '.' in token:
            try:
                b64,sig=token.split('.',1)
                expected_sig=hmac.new(SIGN_SECRET,b64.encode(),hashlib.sha256).hexdigest()
                if hmac.compare_digest(expected_sig,sig):
                    payload=json.loads(base64.urlsafe_b64decode(b64.encode()).decode())
                    if payload.get('exp',0)>time.time():
                        try:
                            with self.db() as db:
                                db.execute('INSERT OR IGNORE INTO users(id,email,name,password,plan,created) VALUES(?,?,?,?,?,?)',
                                           (payload['id'],payload.get('email','user@tableflow.app'),payload.get('name','User'),'signed-session',payload.get('plan','starter'),payload.get('created',time.time())))
                        except Exception:pass
                        return {'id':payload['id'],'name':payload.get('name','User'),'email':payload.get('email','user@tableflow.app'),'plan':payload.get('plan','starter'),'created':payload.get('created',time.time())}
            except Exception:pass
        with self.db() as db:
            row=db.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE digest=? AND expires>?',(digest,time.time())).fetchone()
        return self.public(row) if row else None
    def logout(self,cookie):
        try:c=SimpleCookie();c.load(cookie or '');token=c['tableflow_session'].value
        except (KeyError,ValueError,CookieError):return
        digest=self.digest(token);REVOKED.add(digest)
        with self.db() as db:db.execute('DELETE FROM sessions WHERE digest=?',(digest,))
    def set_plan(self,uid,plan):
        if plan not in ('starter','pro','team'):raise ValueError('Unknown plan.')
        with self.db() as db:
            db.execute('UPDATE users SET plan=? WHERE id=?',(plan,uid));row=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
        return self.public(row) if row else {'id':uid,'name':'User','email':'user@tableflow.app','plan':plan,'created':time.time()}
    def create_share(self,uid,jid,hours):
        if hours not in (1,24,168):raise ValueError('Choose 1 hour, 24 hours or 7 days.')
        token=secrets.token_urlsafe(32);sid=secrets.token_hex(16);now=time.time()
        with self.db() as db:db.execute('INSERT INTO shares(id,digest,user_id,job_id,expires,created) VALUES(?,?,?,?,?,?)',(sid,self.digest(token),uid,jid,now+hours*3600,now))
        return dict(id=sid,token=token,expires=now+hours*3600,created=now,job_id=jid)
    def resolve_share(self,token):
        with self.db() as db:row=db.execute('SELECT * FROM shares WHERE digest=? AND revoked=0 AND expires>?',(self.digest(token),time.time())).fetchone()
        return dict(row) if row else None
    def shares(self,uid):
        with self.db() as db:return [dict(r) for r in db.execute('SELECT id,job_id,expires,created,revoked FROM shares WHERE user_id=? ORDER BY created DESC',(uid,))]
    def revoke(self,uid,sid):
        with self.db() as db:db.execute('UPDATE shares SET revoked=1 WHERE id=? AND user_id=?',(sid,uid))
