from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

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

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    background_url = db.Column(db.String(200))
    admin_password_hash = db.Column(db.String(128))
