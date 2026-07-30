"""AqilUstun Bridge — Web Admin Dashboard (Flask)

Ushbu server orqali:
1. AI System Prompt (prompt.txt) ni brauzerda real-time tahrirlash va saqlash;
2. Google Gemini API Key ni yangilash imkoniyati bor.

Kirish xavfsizligi:
Login: admin
Parol: A1tech2026!@
"""

import os
import re
from functools import wraps
from flask import Flask, render_template_string, request, jsonify, Response

app = Flask(__name__)

# Admin Login va Paroli
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "A1tech2026!@"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, "prompt.txt")
CONFIG_FILE = os.path.join(BASE_DIR, "config.py")


def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Kirish rad etildi. Login yoki parol xato!",
                401,
                {"WWW-Authenticate": 'Basic realm="AqilUstun Bridge Admin Dashboard"'},
            )
        return f(*args, **kwargs)

    return decorated


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AqilUstun Bridge — Admin Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --panel: #1e293b;
            --border: #334155;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --success: #10b981;
            --text: #f8fafc;
            --muted: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 32px 24px; min-height: 100vh; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
        h1 { font-size: 26px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .user-info { display: flex; align-items: center; gap: 12px; }
        .grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .card-title { font-size: 16px; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 8px; }
        textarea { width: 100%; height: 320px; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 16px; font-size: 14px; line-height: 1.6; resize: vertical; outline: none; }
        textarea:focus { border-color: var(--accent); }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        input[type="password"], input[type="text"] { width: 100%; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 14px 16px; font-size: 14px; outline: none; }
        input:focus { border-color: var(--accent); }
        .btn { background: var(--accent); color: white; border: none; border-radius: 10px; padding: 12px 24px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .status-badge { background: rgba(16, 185, 129, 0.15); color: var(--success); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
        .admin-badge { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.3); }
        .toast { position: fixed; bottom: 24px; right: 24px; background: var(--success); color: white; padding: 14px 28px; border-radius: 10px; font-weight: 600; display: none; box-shadow: 0 10px 25px rgba(0,0,0,0.4); z-index: 999; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>AqilUstun Bridge — Admin Dashboard</h1>
                <p style="color: var(--muted); font-size: 13px; margin-top: 4px;">AI System Prompt & Gemini API Key Management</p>
            </div>
            <div class="user-info">
                <div class="admin-badge">👤 Admin: admin</div>
                <div class="status-badge">● Bridge Online</div>
            </div>
        </header>

        <div class="grid">
            <!-- System Prompt Card -->
            <div class="card">
                <div>
                    <div class="card-header">
                        <div class="card-title">🤖 AI System Prompt (prompt.txt)</div>
                    </div>
                    <form id="promptForm">
                        <textarea id="promptText" name="prompt" placeholder="AI System Prompt matnini bering...">{{ prompt }}</textarea>
                        <div style="margin-top: 20px; text-align: right;">
                            <button type="submit" class="btn">💾 Promptni Saqlash</button>
                        </div>
                    </form>
                </div>
            </div>

            <!-- Gemini API Key Card -->
            <div class="card">
                <div>
                    <div class="card-header">
                        <div class="card-title">🔑 Google Gemini API Key (config.py)</div>
                    </div>
                    <form id="configForm">
                        <div class="form-group">
                            <label>Gemini API Key</label>
                            <input type="password" id="geminiKey" name="gemini_key" value="{{ gemini_key }}" placeholder="AIzaSy...">
                        </div>
                        <p style="color: var(--muted); font-size: 12px; line-height: 1.5; margin-bottom: 20px;">
                            Ushbu API Key Google Gemini Live API bilan muloqot o'rnatish uchun ishlatiladi. Kalit yangilangach <strong>"API Key Saqlash"</strong> tugmasini bosing.
                        </p>
                        <div style="text-align: right;">
                            <button type="submit" class="btn">🔑 API Key Saqlash</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Saqlandi!</div>

    <script>
        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }

        document.getElementById('promptForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('promptText').value;
            const res = await fetch('/api/prompt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: text})
            });
            if (res.ok) showToast('✅ System Prompt muvaffaqiyatli saqlandi!');
        });

        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const key = document.getElementById('geminiKey').value;
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({gemini_key: key})
            });
            if (res.ok) showToast('✅ Gemini API Key muvaffaqiyatli saqlandi!');
        });
    </script>
</body>
</html>
"""


def read_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def read_gemini_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r'GEMINI_API_KEY\s*=\s*["\'](.*?)["\']', content)
            if m:
                return m.group(1)
    return ""


@app.route("/")
@requires_auth
def index():
    prompt = read_prompt()
    gemini_key = read_gemini_key()
    return render_template_string(
        HTML_TEMPLATE, prompt=prompt, gemini_key=gemini_key
    )


@app.route("/api/prompt", methods=["POST"])
@requires_auth
def save_prompt():
    data = request.get_json()
    new_prompt = data.get("prompt", "")
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(new_prompt)
    print("[Dashboard] System Prompt yangilandi")
    return jsonify({"status": "ok"})


@app.route("/api/config", methods=["POST"])
@requires_auth
def save_config():
    data = request.get_json()
    new_key = data.get("gemini_key", "")
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        if "GEMINI_API_KEY" in content:
            new_content = re.sub(
                r'GEMINI_API_KEY\s*=\s*["\'].*?["\']',
                f'GEMINI_API_KEY = "{new_key}"',
                content,
            )
        else:
            new_content = content.rstrip() + f'\nGEMINI_API_KEY = "{new_key}"\n'
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
    print("[Dashboard] GEMINI_API_KEY yangilandi")
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("[Dashboard] AqilUstun Bridge Admin Dashboard running on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
