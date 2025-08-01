from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os
import shutil
from models import db, Player, Stat, Item, SiteConfig, ItemTemplate
from config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pw = request.form.get('password')
        config = SiteConfig.query.first()
        if config and check_password_hash(config.admin_password_hash, pw):
            session['admin'] = True
            return redirect(url_for('admin.dashboard'))
        return render_template('admin/login.html', error="密碼錯誤")
    return render_template('admin/login.html')

@admin_bp.route('/')
@admin_required
def dashboard():
    players = Player.query.all()
    return render_template('admin/dashboard.html', players=players)

@admin_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_player():
    if request.method == 'POST':
        return handle_player_form()
    templates = ItemTemplate.query.all()
    return render_template('admin/add_player.html', edit_mode=False, templates=templates)

@admin_bp.route('/edit/<int:player_id>', methods=['GET', 'POST'])
@admin_required
def edit_player(player_id):
    player = Player.query.get_or_404(player_id)
    if request.method == 'POST':
        return handle_player_form(player)
    templates = ItemTemplate.query.all()
    return render_template('admin/add_player.html', edit_mode=True, player=player, templates=templates)

@admin_bp.route('/delete/<int:player_id>')
@admin_required
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    # 刪除頭像文件
    if player.avatar_url and player.avatar_url != "default.png":
        try:
            # 從 uploads 資料夾刪除
            os.remove(os.path.join(Config.AVATAR_FOLDER, player.avatar_url))
            # 從 static 資料夾刪除
            os.remove(os.path.join(Config.STATIC_AVATARS, player.avatar_url))
        except:
            pass
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/config', methods=['GET', 'POST'])
@admin_required
def config():
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
            
            if background_file and background_file.filename and Config.allowed_file(background_file.filename):
                filename = secure_filename(background_file.filename)
                # 儲存到 uploads 資料夾
                upload_path = os.path.join(Config.BACKGROUND_FOLDER, filename)
                background_file.save(upload_path)
                # 複製到 static 資料夾供網頁訪問
                static_path = os.path.join(Config.STATIC_BACKGROUNDS, filename)
                shutil.copy2(upload_path, static_path)
                config.background_url = f"/static/backgrounds/{filename}"
                message = "背景圖片已成功更新！"
            elif preset_bg:
                config.background_url = preset_bg
                message = "背景已更新為預設背景！"
            else:
                error = "請選擇有效的背景圖片或預設背景"
                
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
    
    return render_template('admin/config.html', config=config, message=message, error=error)

@admin_bp.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('main.index'))

def handle_player_form(player=None):
    name = request.form['name']
    bio = request.form['bio']
    pw = request.form.get('password')
    avatar_file = request.files.get('avatar')
    
    # 處理頭像上傳
    filename = None
    if avatar_file and avatar_file.filename and Config.allowed_file(avatar_file.filename):
        filename = secure_filename(avatar_file.filename)
        # 儲存到 uploads 資料夾
        upload_path = os.path.join(Config.AVATAR_FOLDER, filename)
        avatar_file.save(upload_path)
        # 複製到 static 資料夾供網頁訪問
        static_path = os.path.join(Config.STATIC_AVATARS, filename)
        shutil.copy2(upload_path, static_path)
    
    if player:  # 編輯模式
        player.name = name
        player.bio = bio
        if pw:
            player.set_password(pw)
        if filename:
            # 刪除舊頭像
            if player.avatar_url and player.avatar_url != "default.png":
                try:
                    os.remove(os.path.join(Config.AVATAR_FOLDER, player.avatar_url))
                    os.remove(os.path.join(Config.STATIC_AVATARS, player.avatar_url))
                except:
                    pass
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
    return redirect(url_for('admin.dashboard'))

# 道具模板管理
@admin_bp.route('/item-templates')
@admin_required
def item_templates():
    templates = ItemTemplate.query.all()
    return render_template('admin/item_templates.html', templates=templates)

@admin_bp.route('/add-item-template', methods=['POST'])
@admin_required
def add_item_template():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if name:
        # 檢查是否已存在
        existing = ItemTemplate.query.filter_by(name=name).first()
        if not existing:
            template = ItemTemplate(name=name, description=description)
            db.session.add(template)
            db.session.commit()
    
    return redirect(url_for('admin.item_templates'))

@admin_bp.route('/delete-item-template/<int:template_id>')
@admin_required
def delete_item_template(template_id):
    template = ItemTemplate.query.get_or_404(template_id)
    db.session.delete(template)
    db.session.commit()
    return redirect(url_for('admin.item_templates'))

# 批量操作
@admin_bp.route('/bulk-operations')
@admin_required
def bulk_operations():
    players = Player.query.all()
    templates = ItemTemplate.query.all()
    return render_template('admin/bulk_operations.html', players=players, templates=templates)

@admin_bp.route('/bulk-add-stat', methods=['POST'])
@admin_required
def bulk_add_stat():
    stat_name = request.form.get('stat_name', '').strip()
    stat_value = request.form.get('stat_value', 0)
    selected_players = request.form.getlist('players')
    
    if stat_name and selected_players:
        for player_id in selected_players:
            player = Player.query.get(player_id)
            if player:
                # 檢查是否已有這個數值
                existing_stat = Stat.query.filter_by(player_id=player_id, name=stat_name).first()
                if existing_stat:
                    existing_stat.value += int(stat_value)
                else:
                    new_stat = Stat(name=stat_name, value=int(stat_value), player_id=player_id)
                    db.session.add(new_stat)
        
        db.session.commit()
    
    return redirect(url_for('admin.bulk_operations'))

@admin_bp.route('/bulk-add-item', methods=['POST'])
@admin_required
def bulk_add_item():
    template_id = request.form.get('template_id')
    item_count = request.form.get('item_count', 1)
    selected_players = request.form.getlist('players')
    
    if template_id and selected_players:
        template = ItemTemplate.query.get(template_id)
        if template:
            for player_id in selected_players:
                player = Player.query.get(player_id)
                if player:
                    # 檢查是否已有這個道具
                    existing_item = Item.query.filter_by(player_id=player_id, name=template.name).first()
                    if existing_item:
                        existing_item.count += int(item_count)
                    else:
                        new_item = Item(
                            name=template.name, 
                            count=int(item_count), 
                            description=template.description,
                            player_id=player_id
                        )
                        db.session.add(new_item)
            
            db.session.commit()
    
    return redirect(url_for('admin.bulk_operations'))

# 修改數值的 API
@admin_bp.route('/modify-stat/<int:stat_id>', methods=['POST'])
@admin_required
def modify_stat(stat_id):
    from flask import jsonify
    stat = Stat.query.get_or_404(stat_id)
    change_value = request.form.get('change_value', 0)
    
    try:
        change_value = int(change_value)
        stat.value += change_value
        db.session.commit()
        return jsonify({'success': True, 'new_value': stat.value})
    except:
        return jsonify({'success': False}), 400
