import os
from flask import Flask
from werkzeug.security import generate_password_hash
# 新增：日誌
import logging
from logging.handlers import RotatingFileHandler, SysLogHandler

# 導入設定和模型
from config import Config
from models import db, SiteConfig

# 導入路由
from routes.main import main_bp
from routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    
    # 根據環境變數選擇配置
    if os.environ.get('FLASK_ENV') == 'production':
        from production_config import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(Config)
    
    # 設定檔案上傳大小限制
    app.config['MAX_CONTENT_LENGTH'] = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)

    # 初始化 AUDIT 日誌（只記錄審計訊息，如密碼變更）
    class AuditOnlyFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            try:
                msg = record.getMessage()
                return isinstance(msg, str) and msg.startswith('AUDIT ')
            except Exception:
                return False

    # 檔案日誌：logs/audit.log（不含明文密碼）
    try:
        os.makedirs('logs', exist_ok=True)
        file_handler_exists = any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers)
        if not file_handler_exists:
            fh = RotatingFileHandler('logs/audit.log', maxBytes=1_000_000, backupCount=5, encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
            fh.addFilter(AuditOnlyFilter())
            app.logger.addHandler(fh)
    except Exception:
        pass

    # Syslog（NAS 後台可見）。優先使用 /dev/log，其次使用環境變數 SYSLOG_HOST:SYSLOG_PORT
    syslog_handler = None
    try:
        use_syslog = os.environ.get('AUDIT_SYSLOG', '1') == '1'  # 預設開啟，可用 AUDIT_SYSLOG=0 關閉
        if use_syslog:
            if os.path.exists('/dev/log'):
                # 大多數 NAS（Synology/QNAP Docker）可用
                syslog_handler = SysLogHandler(address='/dev/log')
            elif os.environ.get('SYSLOG_HOST'):
                host = os.environ['SYSLOG_HOST']
                port = int(os.environ.get('SYSLOG_PORT', '514'))
                syslog_handler = SysLogHandler(address=(host, port))
            if syslog_handler:
                syslog_handler.setFormatter(logging.Formatter('%(message)s'))
                syslog_handler.addFilter(AuditOnlyFilter())
                app.logger.addHandler(syslog_handler)
    except Exception:
        # 若 syslog 未就緒，不影響應用
        pass

    # 敏感審計 logger（可含明文密碼）：只送 Syslog，預設不寫入檔案
    try:
        audit_sensitive = logging.getLogger('audit_sensitive')
        audit_sensitive.setLevel(logging.INFO)
        audit_sensitive.propagate = False  # 避免傳遞到其他處理器
        if syslog_handler is not None:
            # 另建一個 handler 寫入相同 syslog 目標，但不加過濾或自訂前綴
            sensitive_syslog = SysLogHandler(address=syslog_handler.address)
            sensitive_syslog.setFormatter(logging.Formatter('%(message)s'))
            # 不加 AuditOnlyFilter，允許 AUDIT_SENSITIVE 訊息通過
            audit_sensitive.addHandler(sensitive_syslog)
        # 如需寫入檔案，透過環境變數開啟，避免與一般 audit.log 混在一起
        if os.environ.get('AUDIT_PLAINTEXT_FILE') == '1':
            sfh = RotatingFileHandler('logs/audit_sensitive.log', maxBytes=1_000_000, backupCount=3, encoding='utf-8')
            sfh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
            audit_sensitive.addHandler(sfh)
    except Exception:
        pass

    # 設定 Flask 內建 logger 等級
    app.logger.setLevel(logging.INFO)
    
    # 初始化資料庫
    db.init_app(app)
    
    # 註冊藍圖
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # 初始化資料夾
    Config.init_folders()
    
    return app

def setup_database(app):
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # 檢查是否已有配置
        config = SiteConfig.query.first()
        if not config:
            config = SiteConfig(
                background_url='/static/backgrounds/default.jpg',
                admin_password_hash=generate_password_hash('ykhzYhQVXzFOvXn')
            )
            db.session.add(config)
            db.session.commit()

if __name__ == '__main__':
    app = create_app()
    
    # 初始化資料庫
    setup_database(app)
    
    # 啟動應用
    app.run(debug=True, port=5001, host='0.0.0.0')
    #app.run(debug=True, port=80, host='0.0.0.0')
