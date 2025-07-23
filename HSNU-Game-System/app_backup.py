import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SECRET_KEY'] = 'secret'
db = SQLAlchemy(app)

AVATAR_FOLDER = os.path.join("static", "avatars")
os.makedirs(AVATAR_FOLDER, exist_ok=True)

# --- Models ---
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    avatar_url = db.Column(db.String(100))
    bio = db.Column(db.Text)
    password_hash = db.Column(db.String(128))
    stats = db.relationship('Stat', backref='player', cascade="all, delete-orphan")
    items = db.relationship('Item', backref='player', cascade="all, delete-orphan")

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Stat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    value = db.Column(db.Integer)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    count = db.Column(db.Integer)
    description = db.Column(db.Text)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    background_url = db.Column(db.String(200))
    admin_password_hash = db.Column(db.String(128))


# --- Templates ---
index_html = """<!DOCTYPE html>
<html>
<head>
    <title>角色卡系統</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: url('{{ background_url }}') center/cover no-repeat fixed;
            font-family: '微軟正黑體', Arial, sans-serif;
            backdrop-filter: blur(5px);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .player-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .player-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .player-card:hover {
            transform: translateY(-5px);
        }
        .avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 15px;
            border: 3px solid #ddd;
        }
        .player-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .player-bio {
            color: #666;
            margin-bottom: 15px;
            line-height: 1.4;
        }
        .password-form {
            display: flex;
            gap: 10px;
        }
        .password-input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        .view-btn {
            padding: 8px 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .view-btn:hover {
            background: #0056b3;
        }
        .admin-link {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 角色卡系統</h1>
        {% if not players %}
            <p style="text-align: center; color: #666; font-size: 1.2em;">目前沒有角色，請聯繫管理員新增角色。</p>
        {% else %}
            <div class="player-grid">
            {% for player in players %}
                <div class="player-card">
                    <img src="{{ url_for('static', filename='avatars/' + player.avatar_url) }}" 
                         class="avatar" alt="{{ player.name }}的頭像">
                    <div class="player-name">{{ player.name }}</div>
                    <div class="player-bio">{{ player.bio or '這個角色還沒有簡介...' }}</div>
                    <form method="POST" action="{{ url_for('view_player', player_id=player.id) }}" class="password-form">
                        <input type="password" name="pw" placeholder="輸入角色密碼" class="password-input" required>
                        <button type="submit" class="view-btn">查看詳細</button>
                    </form>
                </div>
            {% endfor %}
            </div>
        {% endif %}
    </div>
    <a href="{{ url_for('admin_login') }}" class="admin-link">🔧 管理員</a>
</body>
</html>"""

player_html = """<!DOCTYPE html>
<html>
<head>
    <title>{{ player.name }} - 角色詳細資料</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: url('{{ background_url }}') center/cover no-repeat fixed;
            font-family: '微軟正黑體', Arial, sans-serif;
            backdrop-filter: blur(5px);
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .avatar {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 15px;
            border: 4px solid #007bff;
        }
        .player-name {
            font-size: 2.5em;
            color: #333;
            margin-bottom: 10px;
        }
        .player-bio {
            font-size: 1.1em;
            color: #666;
            line-height: 1.5;
            max-width: 600px;
            margin: 0 auto;
        }
        .stats-section, .items-section {
            margin: 30px 0;
        }
        .section-title {
            font-size: 1.8em;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #007bff;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .stat-name {
            font-size: 1em;
            margin-bottom: 8px;
            opacity: 0.9;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        .items-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .item-card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .item-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
            border-color: #007bff;
        }
        .item-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
            margin-bottom: 5px;
        }
        .item-count {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        .item-description {
            color: #666;
            font-size: 0.9em;
            line-height: 1.4;
            display: none;
        }
        .item-card.expanded .item-description {
            display: block;
        }
        .back-btn {
            display: inline-block;
            margin-top: 30px;
            padding: 12px 24px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s ease;
        }
        .back-btn:hover {
            background: #545b62;
        }
        .no-data {
            text-align: center;
            color: #999;
            font-style: italic;
            padding: 20px;
        }
    </style>
    <script>
        function toggleItem(card) {
            card.classList.toggle('expanded');
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="{{ url_for('static', filename='avatars/' + player.avatar_url) }}" 
                 class="avatar" alt="{{ player.name }}的頭像">
            <div class="player-name">{{ player.name }}</div>
            <div class="player-bio">{{ player.bio or '這個角色還沒有簡介...' }}</div>
        </div>

        <div class="stats-section">
            <div class="section-title">📊 角色數值</div>
            {% if player.stats %}
                <div class="stats-grid">
                {% for stat in player.stats %}
                    <div class="stat-card">
                        <div class="stat-name">{{ stat.name }}</div>
                        <div class="stat-value">{{ stat.value }}</div>
                    </div>
                {% endfor %}
                </div>
            {% else %}
                <div class="no-data">暫無數值資料</div>
            {% endif %}
        </div>

        <div class="items-section">
            <div class="section-title">🎒 道具清單</div>
            {% if player.items %}
                <div class="items-grid">
                {% for item in player.items %}
                    <div class="item-card" onclick="toggleItem(this)">
                        <div class="item-name">{{ item.name }}</div>
                        <div class="item-count">x{{ item.count }}</div>
                        <div class="item-description">{{ item.description or '沒有描述' }}</div>
                    </div>
                {% endfor %}
                </div>
                <p style="color: #666; font-size: 0.9em; margin-top: 15px;">💡 點擊道具卡片查看詳細描述</p>
            {% else %}
                <div class="no-data">暫無道具</div>
            {% endif %}
        </div>

        <a href="{{ url_for('index') }}" class="back-btn">← 回到角色列表</a>
    </div>
</body>
</html>"""

admin_login_html = """<!DOCTYPE html>
<html>
<head>
    <title>管理員登入</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: '微軟正黑體', Arial, sans-serif;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        h2 {
            color: #333;
            margin-bottom: 30px;
            font-size: 1.8em;
        }
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 6px;
            margin-bottom: 20px;
            border: 1px solid #f5c6cb;
        }
        .form-group {
            margin-bottom: 20px;
        }
        input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        button:hover {
            background: #0056b3;
        }
        .back-link {
            margin-top: 20px;
            display: block;
            color: #666;
            text-decoration: none;
        }
        .back-link:hover {
            color: #007bff;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🔐 管理員登入</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <div class="form-group">
                <input name="password" type="password" placeholder="輸入管理員密碼" required>
            </div>
            <button type="submit">登入</button>
        </form>
        <a href="{{ url_for('index') }}" class="back-link">← 回到首頁</a>
    </div>
</body>
</html>"""

admin_dashboard_html = """<!DOCTYPE html>
<html>
<head>
    <title>管理員控制台</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: '微軟正黑體', Arial, sans-serif;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .actions {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-block;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-primary:hover {
            background: #0056b3;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover {
            background: #1e7e34;
        }
        .btn-warning {
            background: #ffc107;
            color: #212529;
        }
        .btn-warning:hover {
            background: #e0a800;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover {
            background: #c82333;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover {
            background: #545b62;
        }
        .players-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .player-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .player-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .player-bio {
            color: #666;
            margin-bottom: 15px;
        }
        .player-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛠️ 管理員控制台</h1>
        
        <div class="actions">
            <a href="{{ url_for('admin_add_player') }}" class="btn btn-success">➕ 新增角色</a>
            <a href="{{ url_for('admin_config') }}" class="btn btn-warning">⚙️ 系統設定</a>
            <a href="{{ url_for('index') }}" class="btn btn-primary">🏠 回到首頁</a>
            <a href="{{ url_for('admin_logout') }}" class="btn btn-secondary">🚪 登出</a>
        </div>

        <h2>角色管理</h2>
        {% if not players %}
            <p style="text-align: center; color: #666;">目前沒有角色，點擊上方「新增角色」來建立第一個角色。</p>
        {% else %}
            <div class="players-grid">
            {% for player in players %}
                <div class="player-card">
                    <div class="player-name">{{ player.name }}</div>
                    <div class="player-bio">{{ player.bio or '無簡介' }}</div>
                    <div class="player-actions">
                        <a href="{{ url_for('admin_edit_player', player_id=player.id) }}" 
                           class="btn btn-primary btn-sm">✏️ 編輯</a>
                        <a href="{{ url_for('admin_delete_player', player_id=player.id) }}" 
                           class="btn btn-danger btn-sm" 
                           onclick="return confirm('確定要刪除角色「{{ player.name }}」嗎？')">🗑️ 刪除</a>
                    </div>
                </div>
            {% endfor %}
            </div>
        {% endif %}
    </div>
</body>
</html>"""

admin_add_player_html = """<!DOCTYPE html>
<html>
<head>
    <title>{% if edit_mode %}編輯角色{% else %}新增角色{% endif %}</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: '微軟正黑體', Arial, sans-serif;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h2 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        input, textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        textarea {
            height: 80px;
            resize: vertical;
        }
        .section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .section-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
        }
        .dynamic-fields {
            display: grid;
            gap: 15px;
        }
        .field-row {
            display: grid;
            grid-template-columns: 1fr 100px auto;
            gap: 10px;
            align-items: end;
        }
        .field-row.item-row {
            grid-template-columns: 1fr 100px 2fr auto;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .actions {
            text-align: center;
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .remove-btn {
            padding: 5px 10px;
            font-size: 12px;
        }
    </style>
    <script>
        function addStatField() {
            const container = document.getElementById('stats-container');
            const div = document.createElement('div');
            div.className = 'field-row';
            div.innerHTML = `
                <input name="stat_name" placeholder="數值名稱" value="">
                <input name="stat_value" type="number" placeholder="數值" value="">
                <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
            `;
            container.appendChild(div);
        }

        function addItemField() {
            const container = document.getElementById('items-container');
            const div = document.createElement('div');
            div.className = 'field-row item-row';
            div.innerHTML = `
                <input name="item_name" placeholder="道具名稱" value="">
                <input name="item_count" type="number" placeholder="數量" value="">
                <input name="item_desc" placeholder="道具描述" value="">
                <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
            `;
            container.appendChild(div);
        }

        function removeField(btn) {
            btn.parentElement.remove();
        }
    </script>
</head>
<body>
    <div class="container">
        <h2>{% if edit_mode %}✏️ 編輯角色{% else %}➕ 新增角色{% endif %}</h2>
        
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>角色名稱</label>
                <input name="name" placeholder="輸入角色名稱" value="{{ player.name if player else '' }}" required>
            </div>
            
            <div class="form-group">
                <label>角色簡介</label>
                <textarea name="bio" placeholder="輸入角色簡介...">{{ player.bio if player else '' }}</textarea>
            </div>
            
            <div class="form-group">
                <label>登入密碼</label>
                <input name="password" type="password" placeholder="設定角色登入密碼" {% if not edit_mode %}required{% endif %}>
                {% if edit_mode %}<small style="color: #666;">留空表示不更改密碼</small>{% endif %}
            </div>
            
            <div class="form-group">
                <label>頭像圖片</label>
                <input type="file" name="avatar" accept="image/*">
                {% if edit_mode and player.avatar_url %}<small style="color: #666;">目前頭像：{{ player.avatar_url }}</small>{% endif %}
            </div>

            <div class="section">
                <div class="section-title">📊 角色數值</div>
                <div id="stats-container" class="dynamic-fields">
                    {% if edit_mode and player.stats %}
                        {% for stat in player.stats %}
                        <div class="field-row">
                            <input name="stat_name" placeholder="數值名稱" value="{{ stat.name }}">
                            <input name="stat_value" type="number" placeholder="數值" value="{{ stat.value }}">
                            <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
                        </div>
                        {% endfor %}
                    {% else %}
                        {% for i in range(3) %}
                        <div class="field-row">
                            <input name="stat_name" placeholder="數值名稱" value="">
                            <input name="stat_value" type="number" placeholder="數值" value="">
                            <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
                        </div>
                        {% endfor %}
                    {% endif %}
                </div>
                <button type="button" class="btn btn-success" onclick="addStatField()" style="margin-top: 10px;">+ 新增數值</button>
            </div>

            <div class="section">
                <div class="section-title">🎒 角色道具</div>
                <div id="items-container" class="dynamic-fields">
                    {% if edit_mode and player.items %}
                        {% for item in player.items %}
                        <div class="field-row item-row">
                            <input name="item_name" placeholder="道具名稱" value="{{ item.name }}">
                            <input name="item_count" type="number" placeholder="數量" value="{{ item.count }}">
                            <input name="item_desc" placeholder="道具描述" value="{{ item.description }}">
                            <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
                        </div>
                        {% endfor %}
                    {% else %}
                        {% for i in range(3) %}
                        <div class="field-row item-row">
                            <input name="item_name" placeholder="道具名稱" value="">
                            <input name="item_count" type="number" placeholder="數量" value="">
                            <input name="item_desc" placeholder="道具描述" value="">
                            <button type="button" class="btn btn-danger remove-btn" onclick="removeField(this)">移除</button>
                        </div>
                        {% endfor %}
                    {% endif %}
                </div>
                <button type="button" class="btn btn-success" onclick="addItemField()" style="margin-top: 10px;">+ 新增道具</button>
            </div>

            <div class="actions">
                <button type="submit" class="btn btn-primary">
                    {% if edit_mode %}💾 儲存修改{% else %}✅ 建立角色{% endif %}
                </button>
                <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">取消</a>
            </div>
        </form>
    </div>
</body>
</html>"""

# --- Routes ---
@app.route('/')
def index():
    players = Player.query.all()
    config = SiteConfig.query.first()
    background_url = config.background_url if config else '/static/backgrounds/default.jpg'
    return render_template_string(index_html, players=players, background_url=background_url)

@app.route('/player/<int:player_id>', methods=['POST'])
def view_player(player_id):
    pw = request.form.get('pw')
    player = Player.query.get_or_404(player_id)
    config = SiteConfig.query.first()
    background_url = config.background_url if config else '/static/backgrounds/default.jpg'
    if player.check_password(pw):
        return render_template_string(player_html, player=player, background_url=background_url)
    else:
        return """
        <div style="text-align: center; margin-top: 100px; font-family: '微軟正黑體', Arial, sans-serif;">
            <h2 style="color: #dc3545;">❌ 密碼錯誤</h2>
            <p>請返回重新輸入正確的角色密碼</p>
            <a href="/" style="color: #007bff; text-decoration: none;">← 回到角色列表</a>
        </div>
        """

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('password')
        config = SiteConfig.query.first()
        if config and check_password_hash(config.admin_password_hash, pw):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template_string(admin_login_html, error="密碼錯誤")
    return render_template_string(admin_login_html)

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    players = Player.query.all()
    return render_template_string(admin_dashboard_html, players=players)

@app.route('/admin/add', methods=['GET', 'POST'])
def admin_add_player():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        return handle_player_form()
    return render_template_string(admin_add_player_html, edit_mode=False)

@app.route('/admin/edit/<int:player_id>', methods=['GET', 'POST'])
def admin_edit_player(player_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    player = Player.query.get_or_404(player_id)
    if request.method == 'POST':
        return handle_player_form(player)
    return render_template_string(admin_add_player_html, edit_mode=True, player=player)

@app.route('/admin/delete/<int:player_id>')
def admin_delete_player(player_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    player = Player.query.get_or_404(player_id)
    # 刪除頭像文件
    if player.avatar_url and player.avatar_url != "default.png":
        try:
            os.remove(os.path.join(AVATAR_FOLDER, player.avatar_url))
        except:
            pass
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

def handle_player_form(player=None):
    name = request.form['name']
    bio = request.form['bio']
    pw = request.form.get('password')
    avatar_file = request.files.get('avatar')
    
    # 處理頭像上傳
    filename = None
    if avatar_file and avatar_file.filename:
        filename = secure_filename(avatar_file.filename)
        avatar_file.save(os.path.join(AVATAR_FOLDER, filename))
    
    if player:  # 編輯模式
        player.name = name
        player.bio = bio
        if pw:  # 只有在提供新密碼時才更新
            player.set_password(pw)
        if filename:  # 只有在上傳新頭像時才更新
            player.avatar_url = filename
        # 刪除舊的數值和道具
        Stat.query.filter_by(player_id=player.id).delete()
        Item.query.filter_by(player_id=player.id).delete()
    else:  # 新增模式
        player = Player(
            name=name, 
            bio=bio,
            avatar_url=filename or "default.png"
        )
        if pw:
            player.set_password(pw)
        db.session.add(player)
    
    db.session.flush()
    
    # 處理數值
    stat_names = request.form.getlist('stat_name')
    stat_values = request.form.getlist('stat_value')
    for sname, svalue in zip(stat_names, stat_values):
        if sname.strip():
            db.session.add(Stat(
                name=sname.strip(), 
                value=int(svalue) if svalue else 0, 
                player_id=player.id
            ))
    
    # 處理道具
    item_names = request.form.getlist('item_name')
    item_counts = request.form.getlist('item_count')
    item_descs = request.form.getlist('item_desc')
    for iname, icount, idesc in zip(item_names, item_counts, item_descs):
        if iname.strip():
            db.session.add(Item(
                name=iname.strip(), 
                count=int(icount) if icount else 0, 
                description=idesc.strip(), 
                player_id=player.id
            ))
    
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

admin_config_html = """<!DOCTYPE html>
<html>
<head>
    <title>系統設定</title>
    <meta charset="utf-8">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: '微軟正黑體', Arial, sans-serif;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        h2 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .section-title {
            font-size: 1.2em;
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }
        .btn-primary {
            background: #007bff;
            color: white;
        }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .actions {
            text-align: center;
            margin-top: 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        .preview {
            width: 100%;
            height: 200px;
            border-radius: 8px;
            object-fit: cover;
            margin-top: 10px;
        }
        .current-bg {
            text-align: center;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚙️ 系統設定</h2>
        
        <div class="section">
            <div class="section-title">🖼️ 背景設定</div>
            
            {% if config.background_url %}
            <div class="current-bg">
                <p><strong>目前背景：</strong></p>
                <img src="{{ config.background_url }}" class="preview" alt="目前背景">
            </div>
            {% endif %}
            
            <form method="POST" enctype="multipart/form-data">
                <div class="form-group">
                    <label>選擇新背景圖片</label>
                    <input type="file" name="background" accept="image/*">
                    <small style="color: #666;">支援 JPG、PNG、GIF 格式</small>
                </div>
                
                <div class="form-group">
                    <label>或使用預設背景</label>
                    <select name="preset_background">
                        <option value="">-- 選擇預設背景 --</option>
                        <option value="/static/backgrounds/gradient1.jpg">漸層背景 1</option>
                        <option value="/static/backgrounds/gradient2.jpg">漸層背景 2</option>
                        <option value="/static/backgrounds/pattern1.jpg">圖案背景 1</option>
                        <option value="/static/backgrounds/nature1.jpg">自然風景 1</option>
                    </select>
                </div>
                
                <button type="submit" name="action" value="background" class="btn btn-primary">💾 更新背景</button>
            </form>
        </div>

        <div class="section">
            <div class="section-title">🔐 管理員密碼</div>
            <form method="POST">
                <div class="form-group">
                    <label>新管理員密碼</label>
                    <input type="password" name="new_password" placeholder="輸入新的管理員密碼">
                </div>
                
                <div class="form-group">
                    <label>確認新密碼</label>
                    <input type="password" name="confirm_password" placeholder="再次輸入新密碼">
                </div>
                
                <button type="submit" name="action" value="password" class="btn btn-primary">🔑 更新密碼</button>
            </form>
        </div>

        {% if message %}
        <div style="background: #d4edda; color: #155724; padding: 10px; border-radius: 6px; margin: 20px 0;">
            {{ message }}
        </div>
        {% endif %}

        {% if error %}
        <div style="background: #f8d7da; color: #721c24; padding: 10px; border-radius: 6px; margin: 20px 0;">
            {{ error }}
        </div>
        {% endif %}

        <div class="actions">
            <a href="{{ url_for('admin_dashboard') }}" class="btn btn-secondary">← 返回管理台</a>
        </div>
    </div>
</body>
</html>"""

@app.route('/admin/config', methods=['GET', 'POST'])
def admin_config():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig(
            background_url='/static/backgrounds/default.jpg',
            admin_password_hash=generate_password_hash('admin123')
        )
        db.session.add(config)
        db.session.commit()
    
    message = None
    error = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'background':
            background_file = request.files.get('background')
            preset_bg = request.form.get('preset_background')
            
            if background_file and background_file.filename:
                # 上傳自定義背景
                filename = secure_filename(background_file.filename)
                bg_path = os.path.join("static", "backgrounds", filename)
                os.makedirs(os.path.dirname(bg_path), exist_ok=True)
                background_file.save(bg_path)
                config.background_url = f"/static/backgrounds/{filename}"
                message = "背景圖片已成功更新！"
            elif preset_bg:
                # 使用預設背景
                config.background_url = preset_bg
                message = "背景已更新為預設背景！"
            else:
                error = "請選擇背景圖片或預設背景"
                
        elif action == 'password':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password:
                error = "請輸入新密碼"
            elif new_password != confirm_password:
                error = "兩次輸入的密碼不一致"
            elif len(new_password) < 6:
                error = "密碼長度至少需要6個字符"
            else:
                config.admin_password_hash = generate_password_hash(new_password)
                message = "管理員密碼已成功更新！"
        
        if not error:
            db.session.commit()
    
    return render_template_string(admin_config_html, config=config, message=message, error=error)

def setup():
    db.drop_all()
    db.create_all()
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig(
            background_url='/static/backgrounds/bg1.jpg',
            admin_password_hash=generate_password_hash('admin123')
        )
        db.session.add(config)
        db.session.commit()
        print("✅ 初始化完成")

if __name__ == '__main__':
    with app.app_context():
        setup()
    app.run(debug=True, port=5001)
