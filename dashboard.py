"""AqilUstun Bridge — Web Admin Dashboard (Flask)

Ushbu server orqali:
1. System Prompt (prompt.txt) ni brauzerda real-time tahrirlash va saqlash;
2. Gemini API Key va IP sozlamalarini (config.py) yangilash;
3. Qo'ng'iroqlar tarixi va transkriptlarini (logs/) ko'rish imkoniyati bor.

Kirish xavfsizligi:
Login: admin
Parol: A1tech2026!@
"""

import json
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
LOGS_DIR = os.path.join(BASE_DIR, "logs")


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
        body { background: var(--bg); color: var(--text); padding: 24px; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
        h1 { font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .user-info { display: flex; align-items: center; gap: 12px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card { background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .card-title { font-size: 16px; font-weight: 600; color: var(--text); }
        textarea { width: 100%; height: 260px; background: #090d16; border: 1px solid var(--border); border-radius: 10px; color: #e2e8f0; padding: 14px; font-size: 14px; line-height: 1.6; resize: vertical; outline: none; }
        textarea:focus { border-color: var(--accent); }
        .form-group { margin-bottom: 14px; }
        label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        input[type="text"], input[type="password"] { width: 100%; background: #090d16; border: 1px solid var(--border); border-radius: 8px; color: #e2e8f0; padding: 10px 14px; font-size: 14px; outline: none; }
        input:focus { border-color: var(--accent); }
        .btn { background: var(--accent); color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }
        .btn:hover { background: var(--accent-hover); transform: translateY(-1px); }
        .status-badge { background: rgba(16, 185, 129, 0.15); color: var(--success); padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3); }
        .admin-badge { background: rgba(99, 102, 241, 0.15); color: #818cf8; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid rgba(99, 102, 241, 0.3); }
        .toast { position: fixed; bottom: 20px; right: 20px; background: var(--success); color: white; padding: 12px 24px; border-radius: 8px; font-weight: 600; display: none; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .log-item { background: #090d16; border-radius: 8px; padding: 12px; margin-bottom: 10px; border: 1px solid var(--border); }
        .role-user { color: #38bdf8; font-weight: 600; }
        .role-ai { color: #a78bfa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>AqilUstun Bridge — Admin Dashboard</h1>
                <p style="color: var(--muted); font-size: 13px; margin-top: 4px;">System Prompt, API Keys & Call Logs Management</p>
            </div>
            <div class="user-info">
                <div class="admin-badge">👤 Admin: admin</div>
                <div class="status-badge">● Bridge Online</div>
            </div>
        </header>

        <div class="grid">
            <!-- System Prompt Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🤖 AI System Prompt (prompt.txt)</div>
                </div>
                <form id="promptForm">
                    <textarea id="promptText" name="prompt">{{ prompt }}</textarea>
                    <div style="margin-top: 16px; text-align: right;">
                        <button type="submit" class="btn">💾 Promptni Saqlash</button>
                    </div>
                </form>
            </div>

            <!-- Configuration Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Konfiguratsiya & API Key (config.py)</div>
                </div>
                <form id="configForm">
                    <div class="form-group">
                        <label>Server Public IP</label>
                        <input type="text" id="serverIp" name="server_ip" value="{{ config_data.SERVER_IP }}">
                    </div>
                    <div class="form-group">
                        <label>Domofon (KV6114) IP</label>
                        <input type="text" id="kvIp" name="kv_ip" value="{{ config_data.KV6114_IP }}">
                    </div>
                    <div class="form-group">
                        <label>Domofon Admin Paroli</label>
                        <input type="password" id="kvPass" name="kv_pass" value="{{ config_data.KV6114_PASSWORD }}">
                    </div>
                    <div class="form-group">
                        <label>Google Gemini API Key</label>
                        <input type="password" id="geminiKey" name="gemini_key" value="{{ config_data.GEMINI_API_KEY }}">
                    </div>
                    <div style="margin-top: 16px; text-align: right;">
                        <button type="submit" class="btn">🔑 API Key & Config Saqlash</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Recent Logs Card -->
        <div class="card">
            <div class="card-header">
                <div class="card-title">📜 So'nggi Suhbatlar Tarixi (Transkriptlar)</div>
            </div>
            <div id="logsContainer">
                {% if logs %}
                    {% for call in logs %}
                        <div class="log-item">
                            <div style="font-size: 12px; color: var(--muted); margin-bottom: 8px;">🕒 Qo'ng'iroq vaqti: {{ call.call_start }}</div>
                            {% for turn in call.transcript %}
                                <div style="margin-bottom: 4px; font-size: 13px;">
                                    {% if turn.role == 'visitor' %}
                                        <span class="role-user">👤 Tashrifchi:</span> {{ turn.text }}
                                    {% else %}
                                        <span class="role-ai">🤖 Aqilli Ustun:</span> {{ turn.text }}
                                    {% endif %}
                                </div>
                            {% endfor %}
                        </div>
                    {% endfor %}
                {% else %}
                    <p style="color: var(--muted); font-size: 13px;">Hali suhbatlar tarixi mavjud emas.</p>
                {% endif %}
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
            if (res.ok) showToast('✅ Prompt muvaffaqiyatli saqlandi!');
        });

        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                server_ip: document.getElementById('serverIp').value,
                kv_ip: document.getElementById('kvIp').value,
                kv_pass: document.getElementById('kvPass').value,
                gemini_key: document.getElementById('geminiKey').value
            };
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            if (res.ok) showToast('✅ API Key & Config yangilandi!');
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


def read_config():
    data = {
        "SERVER_IP": "195.158.8.44",
        "KV6114_IP": "192.0.0.65",
        "KV6114_PASSWORD": "",
        "GEMINI_API_KEY": "",
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            for key in data:
                m = re.search(fr'^{key}\s*=\s*["\'](.*?)["\']', content, re.M)
                if m:
                    data[key] = m.group(1)
    return data


def read_logs():
    logs = []
    if os.path.exists(LOGS_DIR):
        files = sorted(os.listdir(LOGS_DIR), reverse=True)[:10]
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(LOGS_DIR, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        logs.append(json.load(f))
                except Exception:
                    pass
    return logs


@app.route("/")
@requires_auth
def index():
    prompt = read_prompt()
    config_data = read_config()
    logs = read_logs()
    return render_template_string(
        HTML_TEMPLATE, prompt=prompt, config_data=config_data, logs=logs
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
    new_content = f"""SERVER_IP = "{data.get('server_ip', '')}"

KV6114_IP = "{data.get('kv_ip', '')}"
KV6114_USERNAME = "admin"
KV6114_PASSWORD = "{data.get('kv_pass', '')}"

KH9510_IP = "192.0.0.66"

CALL_STATUS_URL = f"http://{{KV6114_IP}}/ISAPI/VideoIntercom/callStatus?format=json"
POLL_INTERVAL_SECONDS = 1

AI_MICROSERVICE_URL = "http://localhost:5000/talk"

GEMINI_API_KEY = "{data.get('gemini_key', '')}"
"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("[Dashboard] Config & GEMINI_API_KEY yangilandi")
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print(
        "🚀 AqilUstun Bridge Admin Dashboard running on http://0.0.0.0:8000"
    )
    app.run(host="0.0.0.0", port=8000, debug=False)
