import os
import re
import html
import time
import logging
import threading
import webbrowser
from collections import defaultdict
from functools import wraps

# ─────────────────────────────────────────────
# Load .env for localhost (silently ignored on Render)
# ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — env vars set externally (Render etc.)

from flask import Flask, request, jsonify, render_template, abort
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ─────────────────────────────────────────────
# 🔐 CONFIG — loaded from environment variables
# Fallback to hardcoded only for local dev (not recommended for production)
# ─────────────────────────────────────────────
EMAIL        = os.environ.get("CONTACT_EMAIL")
APP_PASSWORD = os.environ.get("CONTACT_APP_PASSWORD")

if not EMAIL or not APP_PASSWORD:
    logger.warning("⚠️  CONTACT_EMAIL or CONTACT_APP_PASSWORD env var is not set. Email sending will fail.")

# ─────────────────────────────────────────────
# CORS — restrict to your own domain in production
# e.g. origins=["https://engineersvilla.com"]
# ─────────────────────────────────────────────
CORS(app, origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","))

# ─────────────────────────────────────────────
# Input limits
# ─────────────────────────────────────────────
MAX_LENGTHS = {
    "firstName": 60,
    "lastName":  60,
    "email":     254,   # RFC 5321 max
    "role":      80,
    "message":   2000,
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)

# ─────────────────────────────────────────────
# Rate limiter — simple in-memory (per IP)
# Replace with Flask-Limiter + Redis for production
# ─────────────────────────────────────────────
RATE_LIMIT_WINDOW  = 60   # seconds
RATE_LIMIT_MAX     = 5    # max requests per window

_rate_store: dict[str, list[float]] = defaultdict(list)

def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_store[ip] if t > window_start]
    _rate_store[ip] = timestamps
    if len(timestamps) >= RATE_LIMIT_MAX:
        return True
    _rate_store[ip].append(now)
    return False

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()
        if is_rate_limited(ip):
            logger.warning(f"Rate limit hit: {ip}")
            return jsonify({"error": "Too many requests. Please wait a moment."}), 429
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def sanitize(value: str) -> str:
    """Strip leading/trailing whitespace and escape HTML entities."""
    return html.escape(str(value).strip())

def validate_payload(data: dict) -> tuple[dict | None, str | None]:
    """Returns (cleaned_data, error_message)."""
    if not isinstance(data, dict):
        return None, "Invalid request body."

    cleaned = {}
    for field, max_len in MAX_LENGTHS.items():
        raw = data.get(field, "")
        if not isinstance(raw, str):
            return None, f"'{field}' must be a string."
        if len(raw) > max_len:
            return None, f"'{field}' exceeds maximum length of {max_len} characters."
        cleaned[field] = sanitize(raw)

    if not cleaned["email"] or not cleaned["message"]:
        return None, "Email and message are required."

    if not EMAIL_REGEX.match(cleaned["email"]):
        return None, "Invalid email address."

    return cleaned, None


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy-policy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms-of-use')
def terms():
    return render_template('terms.html')

@app.route('/partners')
def partners():
    return render_template('partners.html')


# ─────────────────────────────────────────────
# 📩 Contact Form Endpoint
# ─────────────────────────────────────────────
@app.route('/send-message', methods=['POST'])
@rate_limit
def send_message():
    # Enforce Content-Type
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json."}), 415

    raw_data = request.get_json(silent=True)
    if raw_data is None:
        return jsonify({"error": "Malformed JSON body."}), 400

    data, err = validate_payload(raw_data)
    if err:
        return jsonify({"error": err}), 400

    first_name = data["firstName"]
    last_name  = data["lastName"]
    email      = data["email"]
    role       = data["role"]
    message    = data["message"]

    # ✨ HTML Email Template (user values are already HTML-escaped)
    html_body = f"""
<html>
<body style="margin:0;padding:0;background:#06101e;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#06101e;padding:40px 0;">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0" style="background:#0a1628;border-radius:16px;overflow:hidden;">

  <tr>
    <td style="height:4px;background:linear-gradient(90deg,#00c6ff 0%,#0072ff 100%);font-size:0;line-height:0;">&nbsp;</td>
  </tr>

  <tr>
    <td style="padding:28px 36px 22px;border-bottom:1px solid rgba(255,255,255,0.07);">
      <table cellpadding="0" cellspacing="0"><tr>
        <td style="width:44px;height:44px;background:linear-gradient(135deg,#00c6ff,#0072ff);border-radius:10px;text-align:center;vertical-align:middle;font-size:20px;">&#9670;</td>
        <td style="padding-left:14px;">
          <p style="font-size:20px;font-weight:900;font-style:italic;color:#fff;margin:0;">ENGINEERS<span style="color:#1a6fff;">VILLA</span></p>
          <p style="font-size:11px;color:#4a7aad;margin:4px 0 0;letter-spacing:0.07em;text-transform:uppercase;">Building Future-Ready Engineers</p>
        </td>
      </tr></table>
    </td>
  </tr>

  <tr>
    <td style="padding:28px 36px 0;">
      <table cellpadding="0" cellspacing="0" style="margin-bottom:14px;"><tr>
        <td style="background:rgba(0,198,255,0.1);border:1px solid rgba(0,198,255,0.2);border-radius:6px;padding:5px 12px;">
          <span style="font-size:11px;color:#00c6ff;letter-spacing:0.08em;text-transform:uppercase;">&#9679; New Enrollment Enquiry</span>
        </td>
      </tr></table>
      <h1 style="font-size:26px;font-weight:700;color:#fff;margin:0 0 8px;">You&#39;ve received a new message.</h1>
      <p style="font-size:14px;color:#4a7aad;margin:0;">Here are the details.</p>
    </td>
  </tr>

  <tr><td style="padding:0 36px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background:rgba(255,255,255,0.06);font-size:0;">&nbsp;</td></tr></table></td></tr>

  <tr>
    <td style="padding:20px 36px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="48%" valign="top" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px 16px;word-break:break-word;">
            <p style="font-size:11px;color:#4a7aad;margin:0 0 4px;text-transform:uppercase;">Full Name</p>
            <p style="font-size:15px;color:#dbeafe;margin:0;font-weight:600;">{first_name} {last_name}</p>
          </td>
          <td width="4%">&nbsp;</td>
          <td width="48%" valign="top" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px 16px;word-break:break-word;">
            <p style="font-size:11px;color:#4a7aad;margin:0 0 4px;text-transform:uppercase;">Category</p>
            <p style="font-size:15px;color:#dbeafe;margin:0;font-weight:600;">{role}</p>
          </td>
        </tr>
        <tr><td colspan="3" style="height:8px;"></td></tr>
        <tr>
          <td colspan="3" style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px 16px;word-break:break-word;">
            <p style="font-size:11px;color:#4a7aad;margin:0 0 4px;text-transform:uppercase;">Email Address</p>
            <p style="font-size:15px;color:#00c6ff;margin:0;font-weight:500;word-break:break-all;">{email}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <tr>
    <td style="padding:20px 36px;">
      <p style="font-size:11px;color:#4a7aad;margin:0 0 10px;text-transform:uppercase;">Message</p>
      <div style="background:rgba(0,114,255,0.06);border-left:3px solid #0072ff;border-radius:0 10px 10px 0;padding:16px 18px;">
        <p style="font-size:14px;color:#b8d4f0;line-height:1.75;margin:0;white-space:pre-wrap;word-break:break-word;">{message}</p>
      </div>
    </td>
  </tr>

  <tr><td style="padding:0 36px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background:rgba(255,255,255,0.06);font-size:0;">&nbsp;</td></tr></table></td></tr>
  <tr>
    <td style="padding:18px 36px 26px;">
      <p style="font-size:12px;color:#2d5a8a;margin:0;">&#169; 2025 EngineersVilla. All rights reserved.</p>
    </td>
  </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg['From']    = EMAIL
        msg['To']      = EMAIL
        msg['Subject'] = "New Contact Form Submission — EngineersVilla"
        msg['Reply-To'] = email  # ← allows one-click reply to the sender

        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Contact form email sent from {email}")
        return jsonify({"success": True}), 200

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check credentials.")
        return jsonify({"error": "Server configuration error. Please try again later."}), 500
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return jsonify({"error": "Failed to send message. Please try again later."}), 500
    except Exception as e:
        logger.exception("Unexpected error in send_message")
        return jsonify({"error": "An unexpected error occurred."}), 500


# ─────────────────────────────────────────────
# 🚀 Run App
# ─────────────────────────────────────────────
if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    is_render  = os.environ.get("RENDER") is not None  # Render sets this automatically

    # Auto-open browser on localhost only, not on Render
    if not is_render and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()

    app.run(debug=debug_mode, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
