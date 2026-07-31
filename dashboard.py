"""AqilUstun Bridge — Web Admin Dashboard (Flask)

Ushbu server orqali:
1. Sleek HTML Login Forma (admin / A1tech2026!@);
2. AI System Prompt (prompt.txt) ni real-time tahrirlash va saqlash;
3. Saqlangan promptlarni ustun shaklida ko'rish va qayta tahrirlash (Edit);
4. Google Gemini API Key ni yangilash imkoniyati bor.
"""

from datetime import datetime
from functools import wraps
import json
import os
import re
from flask import Flask, Response, jsonify, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "aqilustun-bridge-secret-key-2026!@"

# Admin Login va Paroli
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "A1tech2026!@"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE = os.path.join(BASE_DIR, "prompt.txt")
PROMPT_HISTORY_FILE = os.path.join(BASE_DIR, "prompt_history.json")
CONFIG_FILE = os.path.join(BASE_DIR, "config.py")


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Avtorizatsiyadan o'tilmagan"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


LOGIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kirish — AqilUstun Bridge Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --panel: #1e293b;
            --border: #334155;
            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --text: #f8fafc;
            --muted: #94a3b8;
            --error: #ef4444;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .login-card { background: var(--panel); border: 1px solid var(--border); border-radius: 20px; padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); text-align: center; }
        h1 { font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        p.subtitle { color: var(--muted); font-size: 13px; margin-bottom: 28px; }
        .form-group { margin-bottom: 20px; text-align: left; }
        label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        input[type="text"], input[type="password"] { width: 100%; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 14px 16px; font-size: 14px; outline: none; transition: border-color 0.2s; }
        input:focus { border-color: var(--accent); }
        .btn { width: 100%; background: var(--accent); color: white; border: none; border-radius: 10px; padding: 14px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-top: 8px; }
        .btn:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .error-msg { background: rgba(239, 68, 68, 0.15); color: var(--error); border: 1px solid rgba(239, 68, 68, 0.3); padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; text-align: left; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>AqilUstun Bridge</h1>
        <p class="subtitle">Admin Tizimiga Kirish</p>
        
        {% if error %}
            <div class="error-msg">⚠️ {{ error }}</div>
        {% endif %}

        <form action="/login" method="POST">
            <div class="form-group">
                <label>Login (Foydalanuvchi nomi)</label>
                <input type="text" name="username" placeholder="admin" required autofocus>
            </div>
            <div class="form-group">
                <label>Parol</label>
                <input type="password" name="password" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn">🚀 Tizimga Kirish</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML_TEMPLATE = """
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
            --card-inner: #090d16;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 32px 24px; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
        h1 { font-size: 26px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .user-info { display: flex; align-items: center; gap: 12px; }
        .admin-badge { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.3); }
        .status-badge { background: rgba(16, 185, 129, 0.15); color: var(--success); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
        .btn-logout { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); text-decoration: none; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; transition: all 0.2s; }
        .btn-logout:hover { background: #ef4444; color: white; }

        .card-stack { display: flex; flex-direction: column; gap: 24px; }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 20px; padding: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .card-title { font-size: 18px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 10px; }
        
        .btn-edit-toggle { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); padding: 8px 16px; border-radius: 10px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px; }
        .btn-edit-toggle:hover { background: var(--accent); color: white; transform: translateY(-1px); }
        
        .btn-save { background: var(--accent); color: white; border: none; border-radius: 10px; padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 6px; }
        .btn-save:hover { background: var(--accent-hover); }
        .btn-cancel { background: rgba(148, 163, 184, 0.15); color: var(--muted); border: 1px solid var(--border); border-radius: 10px; padding: 10px 18px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-cancel:hover { background: rgba(148, 163, 184, 0.3); color: white; }

        /* Document Display View Styling */
        .prompt-display-container { font-size: 14px; line-height: 1.7; color: #e2e8f0; padding: 12px 0; }
        .prompt-section-header { font-size: 14px; font-weight: 700; color: #818cf8; background: rgba(99, 102, 241, 0.12); border-left: 3px solid #6366f1; padding: 6px 12px; margin-top: 16px; margin-bottom: 8px; border-radius: 0 8px 8px 0; display: inline-block; letter-spacing: 0.5px; }
        .prompt-section-subheader { font-size: 13px; font-weight: 600; color: #c084fc; margin-top: 12px; margin-bottom: 6px; }
        .prompt-text-block { color: #cbd5e1; margin-bottom: 12px; white-space: pre-wrap; word-break: break-word; }

        .key-view-box { background: var(--card-inner); border: 1px solid var(--border); border-radius: 14px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; font-family: monospace; font-size: 15px; color: #38bdf8; }

        textarea { width: 100%; height: 320px; background: var(--card-inner); border: 1.5px solid var(--accent); border-radius: 14px; color: #f8fafc; padding: 18px; font-size: 14px; line-height: 1.6; resize: vertical; outline: none; margin-bottom: 16px; box-shadow: 0 0 20px rgba(99, 102, 241, 0.15); }
        input[type="password"], input[type="text"] { width: 100%; background: var(--card-inner); border: 1.5px solid var(--accent); border-radius: 12px; color: #f8fafc; padding: 14px 16px; font-size: 14px; outline: none; margin-bottom: 16px; box-shadow: 0 0 15px rgba(99, 102, 241, 0.15); }
        
        .toast { position: fixed; bottom: 24px; right: 24px; background: var(--success); color: white; padding: 14px 28px; border-radius: 12px; font-weight: 600; display: none; box-shadow: 0 10px 25px rgba(0,0,0,0.4); z-index: 999; }
        .edit-actions { display: flex; justify-content: flex-end; gap: 12px; }
        .saved-badge { font-size: 11px; background: rgba(16, 185, 129, 0.15); color: var(--success); padding: 4px 10px; border-radius: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); margin-bottom: 12px; display: inline-block; }
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
                <a href="/logout" class="btn-logout">Chiqish (Logout)</a>
            </div>
        </header>

        <div class="card-stack">
            <!-- System Prompt Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🤖 AI System Prompt Card</div>
                    <button class="btn-edit-toggle" id="promptToggleBtn" onclick="togglePromptEdit()">✏️ Tahrirlash</button>
                </div>
                
                <!-- Display Card View (Read-Only Document Style) -->
                <div id="promptView">
                    <div class="saved-badge">✓ Faol & Saqlangan Tizim Yo'riqnomasi</div>
                    <div id="promptFormattedContent" class="prompt-display-container"></div>
                </div>

                <!-- Form Edit View (Hidden by default, opens only when Tahrirlash is clicked) -->
                <form id="promptEditForm" style="display: none;">
                    <textarea id="promptText" name="prompt" placeholder="AI System Prompt matnini bering...">{{ prompt }}</textarea>
                    <div class="edit-actions">
                        <button type="button" class="btn-cancel" onclick="togglePromptEdit()">❌ Bekor qilish</button>
                        <button type="submit" class="btn-save">💾 Saqlash</button>
                    </div>
                </form>
            </div>

            <!-- Gemini API Key Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔑 Google Gemini API Key Card</div>
                    <button class="btn-edit-toggle" id="configToggleBtn" onclick="toggleConfigEdit()">✏️ Tahrirlash</button>
                </div>
                
                <!-- Display Key View -->
                <div id="configView" class="key-view-box">
                    <span id="keyDisplay">{% if gemini_key %}{{ gemini_key[:6] }}••••••••••••{{ gemini_key[-4:] }}{% else %}Sozlanmagan{% endif %}</span>
                    <span style="color: var(--success); font-size: 12px; font-weight: 600; font-family: 'Inter', sans-serif;">● Faol Kalit</span>
                </div>

                <!-- Form Edit View (Hidden by default) -->
                <form id="configEditForm" style="display: none;">
                    <input type="password" id="geminiKey" name="gemini_key" value="{{ gemini_key }}" placeholder="AIzaSy...">
                    <div class="edit-actions">
                        <button type="button" class="btn-cancel" onclick="toggleConfigEdit()">❌ Bekor qilish</button>
                        <button type="submit" class="btn-save">💾 Saqlash</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">Saqlandi!</div>

    <script>
        const rawPromptData = {{ prompt|tojson }};

        function renderPrompt(raw) {
            if (!raw) return '<em style="color: var(--muted);">Prompt kiritilmagan</em>';
            let lines = raw.split('\\n');
            let resultHtml = '';
            lines.forEach(line => {
                let trimmed = line.trim();
                if (trimmed.startsWith('# ')) {
                    resultHtml += `<div class="prompt-section-header">✦ ${trimmed.substring(2)}</div><br>`;
                } else if (trimmed.startsWith('## ')) {
                    resultHtml += `<div class="prompt-section-subheader">▪ ${trimmed.substring(3)}</div><br>`;
                } else if (trimmed) {
                    resultHtml += `<div class="prompt-text-block">${trimmed}</div>`;
                } else {
                    resultHtml += '<br>';
                }
            });
            return resultHtml;
        }

        document.getElementById('promptFormattedContent').innerHTML = renderPrompt(rawPromptData);

        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 3000);
        }

        function togglePromptEdit() {
            const view = document.getElementById('promptView');
            const form = document.getElementById('promptEditForm');
            const btn = document.getElementById('promptToggleBtn');
            if (form.style.display === 'none') {
                form.style.display = 'block';
                view.style.display = 'none';
                btn.innerText = '❌ Yopish';
                document.getElementById('promptText').focus();
            } else {
                form.style.display = 'none';
                view.style.display = 'block';
                btn.innerText = '✏️ Tahrirlash';
            }
        }

        function toggleConfigEdit() {
            const view = document.getElementById('configView');
            const form = document.getElementById('configEditForm');
            const btn = document.getElementById('configToggleBtn');
            if (form.style.display === 'none') {
                form.style.display = 'block';
                view.style.display = 'none';
                btn.innerText = '❌ Yopish';
                document.getElementById('geminiKey').focus();
            } else {
                form.style.display = 'none';
                view.style.display = 'block';
                btn.innerText = '✏️ Tahrirlash';
            }
        }

        document.getElementById('promptEditForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('promptText').value;
            const res = await fetch('/api/prompt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: text})
            });
            if (res.ok) {
                document.getElementById('promptFormattedContent').innerHTML = renderPrompt(text);
                togglePromptEdit();
                showToast('✅ System Prompt Card muvaffaqiyatli saqlandi!');
            }
        });

        document.getElementById('configEditForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const key = document.getElementById('geminiKey').value;
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({gemini_key: key})
            });
            if (res.ok) {
                const masked = key.length > 10 ? key.substring(0,6) + '••••••••••••' + key.substring(key.length - 4) : '••••••••••••';
                document.getElementById('keyDisplay').innerText = masked;
                toggleConfigEdit();
                showToast('✅ Gemini API Key Card muvaffaqiyatli saqlandi!');
            }
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


def read_history():
    if os.path.exists(PROMPT_HISTORY_FILE):
        try:
            with open(PROMPT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    current = read_prompt()
    if current:
        return [
            {
                "id": 1,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": current,
            }
        ]
    return []


def save_to_history(text):
    history = read_history()
    new_id = len(history) + 1
    new_item = {
        "id": new_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": text,
    }
    history.insert(0, new_item)
    history = history[:10]
    with open(PROMPT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def read_gemini_key():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            m = re.search(r'GEMINI_API_KEY\s*=\s*["\'](.*?)["\']', content)
            if m:
                return m.group(1)
    return ""


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Login yoki parol noto'g'ri! Qaytadan urinib ko'ring."
    return render_template_string(LOGIN_HTML_TEMPLATE, error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    prompt = read_prompt()
    history = read_history()
    gemini_key = read_gemini_key()
    return render_template_string(
        DASHBOARD_HTML_TEMPLATE, prompt=prompt, history=history, gemini_key=gemini_key
    )


@app.route("/api/prompt", methods=["POST"])
@login_required
def save_prompt():
    data = request.get_json()
    new_prompt = data.get("prompt", "")
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(new_prompt)
    save_to_history(new_prompt)
    print("[Dashboard] System Prompt yangilandi va ustunga saqlandi")
    return jsonify({"status": "ok"})


@app.route("/api/config", methods=["POST"])
@login_required
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
    port = getattr(config, "DASHBOARD_PORT", 8000)
    print(f"[Dashboard] AqilUstun Bridge Admin Dashboard running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
