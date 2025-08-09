import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite3'
    SECRET_KEY = 'secret'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 檔案上傳設定
    UPLOAD_FOLDER = os.path.join("uploads")  # 主要上傳資料夾
    AVATAR_FOLDER = os.path.join("uploads", "avatars")  # 頭像資料夾
    BACKGROUND_FOLDER = os.path.join("uploads", "backgrounds")  # 背景資料夾
    
    # 靜態檔案資料夾（用於提供檔案訪問）
    STATIC_AVATARS = os.path.join("static", "avatars")
    STATIC_BACKGROUNDS = os.path.join("static", "backgrounds")
    
    # 允許的檔案類型
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 檔案大小限制（16MB）
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # 確保資料夾存在
    @staticmethod
    def init_folders():
        # 創建上傳資料夾
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.AVATAR_FOLDER, exist_ok=True)
        os.makedirs(Config.BACKGROUND_FOLDER, exist_ok=True)
        
        # 創建靜態資料夾（用於網頁訪問）
        os.makedirs(Config.STATIC_AVATARS, exist_ok=True)
        os.makedirs(Config.STATIC_BACKGROUNDS, exist_ok=True)
        
        # 創建其他必要資料夾
        os.makedirs("instance", exist_ok=True)  # 資料庫資料夾
        os.makedirs("logs", exist_ok=True)      # 日誌資料夾
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
