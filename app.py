import os
import threading
import webbrowser

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from flask import Flask, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/partners')
def partners():
    return render_template('partners.html')

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    is_render  = os.environ.get("RENDER") is not None

    if not is_render and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    app.run(
        debug=debug_mode,
        host="127.0.0.1" if not is_render else "0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
