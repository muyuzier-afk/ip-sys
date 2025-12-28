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
