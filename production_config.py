import os
from config import Config

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # 從環境變數讀取敏感資訊
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-key-change-this'
    
    # 資料庫配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///instance/production.db'
    
    # 安全設定
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 日誌設定
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
