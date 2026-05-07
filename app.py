import os

from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import webbrowser

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
CORS(app)

# 🔐 CONFIG — loaded from environment variables
EMAIL = os.environ.get("CONTACT_EMAIL")
APP_PASSWORD = os.environ.get("CONTACT_APP_PASSWORD")

# 🏠 Serve Frontend
@app.route('/')
def home():
    return render_template('index.html')


# 📩 API: Send Message
@app.route('/send-message', methods=['POST'])
def send_message():
    try:
        data = request.json
        print("Incoming Data:", data)  # DEBUG

        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        email = data.get("email", "")
        role = data.get("role", "")
        message = data.get("message", "")

        # 🚫 Basic validation
        if not email or not message:
            return jsonify({"error": "Email and message are required"}), 400


        # ✨ Professional HTML Email Template
        html = f"""
<html>
<body style="margin:0; padding:0; background:#06101e; font-family:Arial, sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#06101e; padding:40px 0;">
<tr><td align="center">

<table width="580" cellpadding="0" cellspacing="0" style="background:#0a1628; border-radius:16px; overflow:hidden;">

  <!-- TOP ACCENT BAR -->
  <tr>
    <td style="height:4px; background:linear-gradient(90deg,#00c6ff 0%,#0072ff 100%); font-size:0; line-height:0;">&nbsp;</td>
  </tr>

  <!-- HEADER -->
  <tr>
    <td style="padding:28px 36px 22px; border-bottom:1px solid rgba(255,255,255,0.07);">
      <table cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:44px; height:44px; background:linear-gradient(135deg,#00c6ff,#0072ff); border-radius:10px; text-align:center; vertical-align:middle; font-size:20px;">&#9670;</td>
          <td style="padding-left:14px;">
            <p style="font-size:20px; font-weight:900; font-style:italic; color:#ffffff; margin:0; letter-spacing:0.01em; line-height:1;">
              ENGINEERS<span style="color:#1a6fff;">VILLA</span>
            </p>
            <p style="font-size:11px; color:#4a7aad; margin:4px 0 0; letter-spacing:0.07em; text-transform:uppercase;">Building Future-Ready Engineers</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- TITLE -->
  <tr>
    <td style="padding:28px 36px 0;">
      <table cellpadding="0" cellspacing="0" style="margin-bottom:14px;">
        <tr>
          <td style="background:rgba(0,198,255,0.1); border:1px solid rgba(0,198,255,0.2); border-radius:6px; padding:5px 12px;">
            <span style="font-size:11px; color:#00c6ff; letter-spacing:0.08em; text-transform:uppercase;">&#9679; New Enrollment Enquiry</span>
          </td>
        </tr>
      </table>
      <h1 style="font-size:26px; font-weight:700; color:#ffffff; margin:0 0 8px; line-height:1.25;">You've received<br>a new message.</h1>
      <p style="font-size:14px; color:#4a7aad; margin:0;">Here is the details.</p>
    </td>
  </tr>

  <!-- DIVIDER -->
  <tr><td style="padding:0 36px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px; background:rgba(255,255,255,0.06); font-size:0;">&nbsp;</td></tr></table></td></tr>

  <!-- INFO GRID -->
  <tr>
    <td style="padding:20px 36px 0;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <!-- Name -->
          <td width="48%" valign="top" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px 16px; word-break:break-word; overflow-wrap:anywhere;">
            <p style="font-size:11px; color:#4a7aad; margin:0 0 4px; letter-spacing:0.07em; text-transform:uppercase;">Full Name</p>
            <p style="font-size:15px; color:#dbeafe; margin:0; font-weight:600; word-break:break-word; overflow-wrap:anywhere;">{first_name} {last_name}</p>
          </td>
          <td width="4%" style="min-width:8px;">&nbsp;</td>
          <!-- Category -->
          <td width="48%" valign="top" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px 16px; word-break:break-word; overflow-wrap:anywhere;">
            <p style="font-size:11px; color:#4a7aad; margin:0 0 4px; letter-spacing:0.07em; text-transform:uppercase;">Category</p>
            <p style="font-size:15px; color:#dbeafe; margin:0; font-weight:600; word-break:break-word; overflow-wrap:anywhere;">{role}</p>
          </td>
        </tr>
        <tr><td colspan="3" style="height:8px;"></td></tr>
        <!-- Email - full width -->
        <tr>
          <td colspan="3" style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px 16px; word-break:break-word; overflow-wrap:anywhere;">
            <p style="font-size:11px; color:#4a7aad; margin:0 0 4px; letter-spacing:0.07em; text-transform:uppercase;">Email Address</p>
            <p style="font-size:15px; color:#00c6ff; margin:0; font-weight:500; word-break:break-all; overflow-wrap:anywhere;">{email}</p>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- MESSAGE -->
  <tr>
    <td style="padding:20px 36px;">
      <p style="font-size:11px; color:#4a7aad; margin:0 0 10px; letter-spacing:0.07em; text-transform:uppercase;">Message</p>
      <div style="background:rgba(0,114,255,0.06); border-left:3px solid #0072ff; border-radius:0 10px 10px 0; padding:16px 18px;">
        <p style="font-size:14px; color:#b8d4f0; line-height:1.75; margin:0; word-break:break-word; overflow-wrap:anywhere; white-space:pre-wrap;">{message}</p>
      </div>
    </td>
  </tr>

  <!-- FOOTER -->
  <tr>
    <td style="padding:0 36px;"><table width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px; background:rgba(255,255,255,0.06); font-size:0;">&nbsp;</td></tr></table></td>
  </tr>
  <tr>
    <td style="padding:18px 36px 26px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="font-size:12px; color:#2d5a8a;">© 2025 EngineersVilla. All rights reserved.</td>
        </tr>
      </table>
    </td>
  </tr>

</table>

</td></tr>
</table>
</body>
</html>
"""
        # 📧 Email Setup
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = EMAIL
        msg['Subject'] = "📩 EngineersVilla Contact Form Submission"

        msg.attach(MIMEText(html, 'html'))

        # 📡 Send Email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()

        return jsonify({"success": True})

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/partners')
def partners():
    return render_template('partners.html')


# 🚀 Run App
if __name__ == "__main__":
    import os
    import webbrowser

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open("http://127.0.0.1:5000")

    app.run(debug=True)