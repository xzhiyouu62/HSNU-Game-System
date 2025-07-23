# VPS 部署指南

## 資料夾結構

```
角色卡系統/
├── app.py                 # 主應用檔案
├── config.py              # 配置檔案
├── models.py              # 資料庫模型
├── requirements.txt       # 依賴清單
├── uploads/               # 檔案上傳儲存 (重要!)
│   ├── avatars/          # 頭像儲存
│   └── backgrounds/      # 背景圖片儲存
├── static/               # 靜態檔案服務
│   ├── avatars/          # 頭像提供訪問
│   └── backgrounds/      # 背景圖片提供訪問
├── templates/            # HTML 模板
├── routes/               # 路由檔案
├── instance/             # 資料庫檔案
└── logs/                 # 日誌檔案
```

## VPS 部署步驟

### 1. 準備伺服器環境

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 和必要工具
sudo apt install python3 python3-pip python3-venv nginx -y

# 安裝 Git（如果需要）
sudo apt install git -y
```

### 2. 上傳專案檔案

```bash
# 使用 SCP 上傳檔案
scp -r ./角色卡系統 user@your-server-ip:/home/user/

# 或者使用 Git
git clone https://github.com/your-repo/role-card-system.git
```

### 3. 設定 Python 環境

```bash
# 進入專案目錄
cd /home/user/角色卡系統

# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 4. 創建 requirements.txt

```
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Werkzeug==2.3.7
Gunicorn==21.2.0
```

### 5. 設定資料夾權限

```bash
# 確保上傳資料夾有寫入權限
mkdir -p uploads/{avatars,backgrounds}
mkdir -p static/{avatars,backgrounds}
mkdir -p instance logs

# 設定權限
chmod 755 uploads/ static/ instance/ logs/
chmod 755 uploads/avatars uploads/backgrounds
chmod 755 static/avatars static/backgrounds
```

### 6. 創建 Gunicorn 配置檔案

建立 `gunicorn.conf.py`:

```python
bind = "127.0.0.1:5001"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 7. 創建 systemd 服務檔案

建立 `/etc/systemd/system/rolecard.service`:

```ini
[Unit]
Description=Role Card System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/home/user/角色卡系統
Environment="PATH=/home/user/角色卡系統/venv/bin"
ExecStart=/home/user/角色卡系統/venv/bin/gunicorn --config gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### 8. 設定 Nginx

建立 `/etc/nginx/sites-available/rolecard`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替換為您的域名或 IP

    # 靜態檔案
    location /static/ {
        alias /home/user/角色卡系統/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 上傳檔案大小限制
    client_max_body_size 16M;

    # Flask 應用
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 9. 啟動服務

```bash
# 啟用 Nginx 站點
sudo ln -s /etc/nginx/sites-available/rolecard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 啟動 Flask 應用
sudo systemctl daemon-reload
sudo systemctl enable rolecard
sudo systemctl start rolecard

# 檢查狀態
sudo systemctl status rolecard
```

### 10. 設定 SSL（可選但建議）

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 獲取 SSL 證書
sudo certbot --nginx -d your-domain.com
```

## 重要注意事項

### 檔案權限
- `uploads/` 資料夾必須有寫入權限
- 建議將檔案所有者設為 `www-data`

### 安全設定
- 修改 `config.py` 中的 `SECRET_KEY`
- 更改預設管理員密碼
- 設定防火牆規則

### 備份策略
- 定期備份 `instance/` 資料夾（資料庫）
- 備份 `uploads/` 資料夾（上傳的檔案）

### 監控和維護
- 檢查日誌檔案
- 監控磁碟空間使用
- 定期更新系統和依賴

## 故障排除

### 檔案上傳失敗
- 檢查 `uploads/` 資料夾權限
- 確認檔案大小限制設定
- 檢查磁碟空間

### 服務無法啟動
```bash
# 檢查服務狀態
sudo systemctl status rolecard

# 查看日誌
sudo journalctl -u rolecard -f

# 手動測試
source venv/bin/activate
python app.py
```
