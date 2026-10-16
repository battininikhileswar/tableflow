"""AI keys are process environment or account-scoped RAM, never browser storage."""
import os,re,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Small, non-executing .env reader; existing process variables take precedence.
if (ROOT/'.env').is_file():
    for line in (ROOT/'.env').read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:continue
        name,value=line.split('=',1);name=name.strip()
        if name in {'GEMINI_API_KEY','GOOGLE_API_KEY','GEMINI_MODEL','OPENAI_API_KEY','OPENAI_MODEL','PORT','TESSERACT_CMD','TABLEFLOW_DATA'}:
            os.environ.setdefault(name,value.strip().strip('\"\''))
import json
LOCK=threading.RLock();SETTINGS={}

def _data_folder():
    default = '/tmp/tableflow_data' if os.getenv('VERCEL') else str(ROOT/'data')
    p = Path(os.getenv('TABLEFLOW_DATA', default))
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_settings(uid):
    with LOCK: setting=SETTINGS.get(uid,{})
    if not setting.get('key'):
        sf = _data_folder() / 'ai_settings.json'
        if sf.is_file():
            try:
                stored = json.loads(sf.read_text(encoding='utf-8'))
                if uid in stored: setting = stored[uid]
            except Exception: pass
    server_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')
    return {'key':setting.get('key') or server_key,'model':setting.get('model') or os.getenv('GEMINI_MODEL','gemini-3-flash-preview')}

def public_settings(uid):
    settings=get_settings(uid)
    server_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY', '')
    return {'configured':bool(settings['key']),'model':settings['model'],'provider':'Google Gemini','personal_key_in_memory':bool(SETTINGS.get(uid,{}).get('key')),'server_key_available':bool(server_key)}

def update_settings(uid,data):
    sf = _data_folder() / 'ai_settings.json'
    stored = {}
    if sf.is_file():
        try: stored = json.loads(sf.read_text(encoding='utf-8'))
        except Exception: pass
    if data.get('clear') is True:
        with LOCK: SETTINGS.pop(uid,None)
        stored.pop(uid, None)
        try: sf.write_text(json.dumps(stored), encoding='utf-8')
        except Exception: pass
        return public_settings(uid)
    model=data.get('model','gemini-3-flash-preview');key=data.get('api_key','')
    if not isinstance(model,str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',model):raise ValueError('Enter a valid Gemini model ID.')
    if not isinstance(key,str) or len(key)>300 or '\n' in key or '\r' in key:raise ValueError('Invalid API key format.')
    with LOCK:
        old=SETTINGS.get(uid,{})
        entry={'model':model,'key':key.strip() or old.get('key','')}
        SETTINGS[uid]=entry
        stored[uid]=entry
        try: sf.write_text(json.dumps(stored), encoding='utf-8')
        except Exception: pass
    return public_settings(uid)
