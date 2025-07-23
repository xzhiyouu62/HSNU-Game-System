from flask import Blueprint, render_template, request
from models import Player, SiteConfig

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    players = Player.query.all()
    config = SiteConfig.query.first()
    background_url = config.background_url if config else '/static/backgrounds/default.jpg'
    return render_template('index.html', players=players, background_url=background_url)

@main_bp.route('/player/<int:player_id>', methods=['POST'])
def view_player(player_id):
    pw = request.form.get('pw')
    player = Player.query.get_or_404(player_id)
    config = SiteConfig.query.first()
    background_url = config.background_url if config else '/static/backgrounds/default.jpg'
    
    if player.check_password(pw):
        return render_template('player.html', player=player, background_url=background_url)
    else:
        return render_template('error.html', 
                             title="密碼錯誤", 
                             message="請返回重新輸入正確的角色密碼")
