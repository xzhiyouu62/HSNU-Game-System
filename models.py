from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event

db = SQLAlchemy()

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

class ItemTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    background_url = db.Column(db.String(200))
    admin_password_hash = db.Column(db.String(128))

# 新增：後台操作紀錄
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # e.g., player_created, player_updated, player_deleted, config_updated
    entity_type = db.Column(db.String(50), nullable=False)  # e.g., Player, ItemTemplate, Config, Stat, Item
    entity_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), index=True)

# 當有新的審計紀錄寫入時，自動寫到應用程式 logger
@event.listens_for(AuditLog, 'after_insert')
def _auditlog_after_insert(mapper, connection, target):
    try:
        from flask import current_app
        if current_app:
            current_app.logger.info(
                f"AUDIT action={target.action} entity={target.entity_type} id={target.entity_id} desc={target.description}"
            )
    except Exception:
        # 避免因 logger 問題影響主要交易
        pass
