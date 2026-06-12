"""Start EventCore server"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from app.main import app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
