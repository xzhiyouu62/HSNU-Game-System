import os
from flask import Flask
from werkzeug.security import generate_password_hash

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
