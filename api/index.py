import os
import sys
from pathlib import Path

# Set VERCEL environment flag
os.environ['VERCEL'] = '1'

# Add the project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.server import Handler

# Vercel Python runtime entry point
class handler(Handler):
    pass
