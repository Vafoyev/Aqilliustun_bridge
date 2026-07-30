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
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background: var(--bg); color: var(--text); padding: 32px 24px; min-height: 100vh; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
        h1 { font-size: 26px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .user-info { display: flex; align-items: center; gap: 12px; }
        .grid { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; margin-bottom: 32px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); display: flex; flex-direction: column; justify-content: space-between; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .card-title { font-size: 16px; font-weight: 600; color: var(--text); display: flex; align-items: center; gap: 8px; }
        textarea { width: 100%; height: 260px; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 16px; font-size: 14px; line-height: 1.6; resize: vertical; outline: none; }
        textarea:focus { border-color: var(--accent); }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        input[type="password"], input[type="text"] { width: 100%; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 14px 16px; font-size: 14px; outline: none; }
        input:focus { border-color: var(--accent); }
        .btn { background: var(--accent); color: white; border: none; border-radius: 10px; padding: 12px 24px; font-weight: 600; font-size: 14px; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .btn-logout { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); text-decoration: none; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; transition: all 0.2s; }
        .btn-logout:hover { background: #ef4444; color: white; }
        .btn-edit { background: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.4); padding: 6px 14px; font-size: 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
        .btn-edit:hover { background: var(--accent); color: white; }
        .status-badge { background: rgba(16, 185, 129, 0.15); color: var(--success); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
        .admin-badge { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.3); }
        .toast { position: fixed; bottom: 24px; right: 24px; background: var(--success); color: white; padding: 14px 28px; border-radius: 10px; font-weight: 600; display: none; box-shadow: 0 10px 25px rgba(0,0,0,0.4); z-index: 999; }
        
        /* Ustun shaklidagi saqlangan promptlar uslubi */
        .history-section { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .prompt-columns { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; margin-top: 16px; }
        .prompt-column-card { background: #090d16; border: 1px solid var(--border); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between; transition: all 0.2s; }
        .prompt-column-card:hover { border-color: var(--accent); }
        .prompt-column-card.active { border-color: var(--success); background: rgba(16, 185, 129, 0.04); }
        .prompt-time { font-size: 11px; color: var(--muted); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .prompt-preview { font-size: 13px; color: #cbd5e1; line-height: 1.5; max-height: 90px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; margin-bottom: 12px; white-space: pre-wrap; }
        .active-tag { background: rgba(16, 185, 129, 0.2); color: var(--success); font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
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

        <div class="grid">
            <!-- System Prompt Card -->
            <div class="card">
                <div>
                    <div class="card-header">
                        <div class="card-title">🤖 AI System Prompt Tahrirlash</div>
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

        <!-- Saqlangan Promptlar (Ustun shaklida) -->
        <div class="history-section">
            <div class="card-header" style="margin-bottom: 4px;">
                <div class="card-title">📋 Saqlangan Promptlar Ro'yxati (Ustunlar)</div>
            </div>
            <p style="color: var(--muted); font-size: 12px;">Saqlangan prompt ustunidagi "✏️ Tahrirlash" tugmasini bossangiz, u yuqoridagi redaktorga yuklanadi.</p>

            <div class="prompt-columns" id="promptColumns">
                {% for item in history %}
                    <div class="prompt-column-card {% if loop.first %}active{% endif %}">
                        <div>
                            <div class="prompt-time">
                                <span>🕒 {{ item.time }}</span>
                                {% if loop.first %}<span class="active-tag">Joriy Prompt</span>{% endif %}
                            </div>
                            <div class="prompt-preview">{{ item.text }}</div>
                        </div>
                        <div style="text-align: right; margin-top: 8px;">
                            <button class="btn-edit" data-prompt="{{ item.text }}">✏️ Tahrirlash</button>
                        </div>
                    </div>
                {% else %}
                    <p style="color: var(--muted); font-size: 13px; grid-column: 1/-1; padding: 12px 0;">Hali saqlangan promptlar mavjud emas.</p>
                {% endfor %}
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

        document.querySelectorAll('.btn-edit').forEach(button => {
            button.addEventListener('click', function() {
                const text = this.getAttribute('data-prompt');
                const textarea = document.getElementById('promptText');
                textarea.value = text;
                textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
                textarea.focus();
                showToast('📋 Prompt tahrirlash oynasiga yuklandi!');
            });
        });

        document.getElementById('promptForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('promptText').value;
            const res = await fetch('/api/prompt', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: text})
            });
            if (res.ok) {
                showToast('✅ System Prompt muvaffaqiyatli saqlandi!');
                setTimeout(() => { location.reload(); }, 800);
            }
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
    print("[Dashboard] AqilUstun Bridge Admin Dashboard running on http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)
