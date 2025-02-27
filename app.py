from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, session
from wtforms import Form, StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user, UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
import os
from forms import LoginForm, RegisterForm, JoinClubForm, LeaveClubForm, TransferMembershipForm, AddUserForm, DeleteUserForm, InitiateTransferForm, ConfirmTransferForm, AddClubForm, EditClubForm, EditClubLimitForm, DeleteClubForm
from flask_migrate import Migrate
from models import db, User, Club, Membership, TransferRequest
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HPSBNWHVTDs4CwYPPMr8'
app.config['WTF_CSRF_ENABLED'] = False  # 禁用 CSRF 保护
app.config['WTF_CSRF_TIME_LIMIT'] = None  # 移除 CSRF 令牌时间限制
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # 使用适当的数据库URI
app.config['SESSION_COOKIE_SECURE'] = False  # 不使用 HTTPS 时设置为 False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 文件大小限制
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1年缓存

# 初始化扩展
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 定义 Admin 访问权限装饰器
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # 禁止访问
        return f(*args, **kwargs)
    return decorated_function

# 验证文件上传
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 路由定义
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名。', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(username=form.username.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录！', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # 添加日志记录
            print(f"User login attempt - Username: {user.username}, Role: {user.role}")
            
            # 先存储角色，再登录用户
            session['user_role'] = user.role
            login_user(user)
            
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误。', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    session.pop('user_role', None)  # 清除角色信息
    logout_user()
    flash('您已登出。', 'info')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    # 打印调试信息
    print(f"Current user: {current_user.username}")
    print(f"Session role: {session.get('user_role')}")
    print(f"User role: {current_user.role}")
    
    clubs = Club.query.all()
    user_memberships = [membership.club.id for membership in current_user.memberships]
    pending_transfers_count = TransferRequest.query.filter_by(to_user_id=current_user.id, status='pending').count()
    
    # 严格检查管理员权限
    is_admin = current_user.is_admin()
    users = User.query.all() if is_admin else None
    
    return render_template('index.html', 
                         clubs=clubs, 
                         users=users if is_admin else None,
                         user_memberships=user_memberships, 
                         pending_transfers_count=pending_transfers_count)

@app.route('/club/<int:club_id>')
@login_required
def club_details(club_id):
    club = Club.query.get_or_404(club_id)
    return render_template('club_details.html', club=club)

@app.route('/add_club', methods=['GET', 'POST'])
@login_required
def add_club():
    if not current_user.is_admin():
        abort(403)
    
    form = AddClubForm()
    if form.validate_on_submit():
        club_name = form.name.data
        club_description = form.description.data
        existing_club = Club.query.filter_by(name=club_name).first()
        if existing_club:
            flash('该社团已存在。', 'danger')
            return redirect(url_for('add_club'))
        new_club = Club(name=club_name, description=club_description)
        db.session.add(new_club)
        db.session.commit()
        flash('社团已成功添加。', 'success')
        return redirect(url_for('index'))
    return render_template('add_club.html', form=form)

@app.route('/delete_club', methods=['GET', 'POST'])
@login_required
def delete_club():
    if not current_user.is_admin():
        abort(403)
    
    form = DeleteClubForm()
    # 获取要删除的社团ID（如果通过URL参数传递）
    club_id = request.args.get('club_id')
    if club_id:
        club = Club.query.get(club_id)
        if club:
            form.club.choices = [(club.id, club.name)]
            form.club.data = club.id
    else:
        # 获取所有社团作为选项
        form.club.choices = [(club.id, club.name) for club in Club.query.all()]
    
    if form.validate_on_submit():
        club_id = form.club.data
        club_to_delete = Club.query.get(club_id)
        if club_to_delete:
            # 删除社团的所有会员关系
            Membership.query.filter_by(club_id=club_id).delete()
            # 删除社团的所有转让请求
            TransferRequest.query.filter_by(club_id=club_id).delete()
            db.session.delete(club_to_delete)
            db.session.commit()
            flash('课程已成功删除。', 'success')
            return redirect(url_for('index'))
        else:
            flash('未找到该课程。', 'danger')
    
    return render_template('delete_club.html', form=form)

@app.route('/edit_club/<int:club_id>', methods=['GET', 'POST'])
@login_required
def edit_club(club_id):
    if not current_user.is_admin():
        abort(403)
    
    club = Club.query.get_or_404(club_id)
    form = EditClubForm(obj=club)
    
    if form.validate_on_submit():
        club.name = form.name.data
        club.description = form.description.data
        db.session.commit()
        flash('社团信息已更新。', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_club.html', form=form, club=club)

@app.route('/edit_club_limit/<int:club_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_club_limit(club_id):
    club = Club.query.get_or_404(club_id)
    form = EditClubLimitForm(obj=club)
    
    if form.validate_on_submit():
        # 验证新的人数限制不小于当前人数
        if form.member_limit.data < len(club.memberships):
            flash('新的人数限制不能小于当前已选人数！', 'danger')
            return render_template('edit_club_limit.html', form=form, club=club)
            
        club.member_limit = form.member_limit.data
        db.session.commit()
        flash('课程人数限制已更新。', 'success')
        return redirect(url_for('index'))
    
    return render_template('edit_club_limit.html', form=form, club=club)

# 错误处理
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

# 文件上传路由示例
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有文件部分', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('文件上传成功！', 'success')
            return redirect(url_for('uploaded_file', filename=filename))
        else:
            flash('无效的文件类型。', 'danger')
            return redirect(request.url)
    return render_template('upload.html')

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return redirect(url_for('static', filename='uploads/' + filename))

# 加入社团路由
@app.route('/join_club', methods=['POST'])
@login_required
def join_club():
    if current_user.role != 'student':
        flash('只有学生可以加入社团', 'error')
        return redirect(url_for('index'))
    
    club_id = request.form.get('club')
    if not club_id:
        flash('请选择要加入的社团', 'error')
        return redirect(url_for('index'))
    
    club = Club.query.get_or_404(club_id)
    
    # 检查是否已经是社团成员
    existing_membership = Membership.query.filter_by(
        user_id=current_user.id, 
        club_id=club.id
    ).first()
    
    if existing_membership:
        flash('您已经是该社团的成员', 'warning')
        return redirect(url_for('index'))
    
    # 检查社团人数是否已满
    if club.member_limit and len(club.memberships) >= club.member_limit:
        flash('该社团已达到人数上限', 'error')
        return redirect(url_for('index'))
    
    # 创建新的会员关系
    membership = Membership(user_id=current_user.id, club_id=club.id)
    db.session.add(membership)
    
    try:
        db.session.commit()
        flash('成功加入社团！', 'success')
    except:
        db.session.rollback()
        flash('加入社团失败，请稍后重试', 'error')
    
    return redirect(url_for('index'))

# 退出社团路由
@app.route('/leave_club', methods=['GET', 'POST'])
@login_required
def leave_club():
    if current_user.role == 'admin':
        flash('管理员无需退出社团。', 'info')
        return redirect(url_for('index'))
    
    form = LeaveClubForm()
    # 动态加载用户已加入的社团
    form.clubs.choices = [
        (membership.club.id, membership.club.name) 
        for membership in current_user.memberships
    ]
    
    if form.validate_on_submit():
        club_id = form.clubs.data
        membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
        if membership:
            db.session.delete(membership)
            db.session.commit()
            flash('成功退出社团。', 'success')
            return redirect(url_for('index'))
        else:
            flash('未找到相关社团。', 'danger')
    return render_template('leave_club.html', form=form)

# 转让社团名额路由（可选）
@app.route('/transfer_membership', methods=['GET', 'POST'])
@login_required
def transfer_membership():
    if current_user.role == 'admin':
        flash('管理员无法转让社团名额。', 'info')
        return redirect(url_for('index'))
    
    form = TransferMembershipForm(current_user_id=current_user.id)
    # 动态加载用户已加入的社团
    form.current_club.choices = [
        (membership.club.id, membership.club.name) 
        for membership in current_user.memberships
    ]
    # 动态加载目标学生
    form.target_user.choices = [
        (user.id, user.username) 
        for user in User.query.filter(User.id != current_user.id).all()
        if user.role != 'admin'
    ]

    if form.validate_on_submit():
        current_club_id = form.current_club.data
        target_user_id = form.target_user.data

        # 确保目标用户存在且非管理员
        target_user = User.query.get(target_user_id)
        if not target_user or target_user.role == 'admin':
            flash('目标用户无效。', 'danger')
            return redirect(url_for('transfer_membership'))
        
        # 检查目标用户是否已经加入两个社团
        target_memberships = Membership.query.filter_by(user_id=target_user_id).count()
        if target_memberships >= 2:
            flash('目标用户已加入两个社团，无法接收更多名额。', 'warning')
            return redirect(url_for('transfer_membership'))
        
        # 检查当前用户在该社团中的会员关系
        membership = Membership.query.filter_by(user_id=current_user.id, club_id=current_club_id).first()
        if not membership:
            flash('您当前不在该社团中。', 'danger')
            return redirect(url_for('transfer_membership'))
        
        # 检查目标用户是否已在该社团中
        target_membership = Membership.query.filter_by(user_id=target_user_id, club_id=current_club_id).first()
        if target_membership:
            flash('目标用户已在该社团中。', 'warning')
            return redirect(url_for('transfer_membership'))
        
        # 检查目标社团成员数量是否已达上限
        if len(membership.club.memberships) >= 20:
            flash('目标社团已满员，无法转让名额。', 'warning')
            return redirect(url_for('transfer_membership'))
        
        # 执行转让：将当前用户从该社团中移除，目标用户加入
        db.session.delete(membership)
        new_membership = Membership(user_id=target_user_id, club_id=current_club_id)
        db.session.add(new_membership)
        db.session.commit()
        flash('社团名额已成功转让。', 'success')
        return redirect(url_for('index'))

    return render_template('transfer_membership.html', form=form)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# 添加用户路由（仅管理员可访问）
@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin():
        abort(403)
    
    form = AddUserForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('用户名已存在。请选择另一个用户名。', 'danger')
            return redirect(url_for('add_user'))
        new_user = User(
            username=form.username.data,
            role=form.role.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('用户已成功添加。', 'success')
        return redirect(url_for('index'))
    return render_template('add_user.html', form=form)

# 删除用户页面路由
@app.route('/delete_user', methods=['GET'])
@login_required
@admin_required
def delete_user():
    return render_template('delete_user.html')

# 删除用户操作路由
@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user_by_id(user_id):
    user = User.query.get_or_404(user_id)
    
    # 不允许删除管理员
    if user.role == 'admin':
        return jsonify({'error': '不能删除管理员账户'}), 403
    
    try:
        # 删除用户的所有社团关系
        Membership.query.filter_by(user_id=user_id).delete()
        
        # 删除用户的所有转让请求
        TransferRequest.query.filter(
            (TransferRequest.from_user_id == user_id) | 
            (TransferRequest.to_user_id == user_id)
        ).delete()
        
        # 删除用户
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': '用户已成功删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': '删除用户失败'}), 500

# 发起名额转让请求
@app.route('/initiate_transfer', methods=['GET', 'POST'])
@login_required
def initiate_transfer():
    if current_user.is_admin():
        flash('管理员无法进行名额转让。', 'warning')
        return redirect(url_for('index'))
    
    form = InitiateTransferForm()
    
    # 填充社团选择字段
    form.club.choices = [(membership.club.id, membership.club.name) for membership in current_user.memberships]
    
    # 填充目标学生选择字段，排除管理员
    form.target_user.choices = [(user.id, user.username) for user in User.query.filter_by(role='student').all()]
    
    if form.validate_on_submit():
        club_id = form.club.data
        target_user_id = form.target_user.data
        
        # 检查目标学生是否已加入两个社团
        target_memberships = Membership.query.filter_by(user_id=target_user_id).count()
        if target_memberships >= 2:
            flash('目标学生已加入两个社团，无法接受更多名额。', 'warning')
            return redirect(url_for('initiate_transfer'))
        
        # 检查当前用户是否在该社团中
        membership = Membership.query.filter_by(user_id=current_user.id, club_id=club_id).first()
        if not membership:
            flash('您当前不在该社团中。', 'danger')
            return redirect(url_for('initiate_transfer'))
        
        # 检查是否已有待处理的转让请求
        existing_request = TransferRequest.query.filter_by(
            from_user_id=current_user.id,
            to_user_id=target_user_id,
            club_id=club_id,
            status='pending'
        ).first()
        if existing_request:
            flash('已存在一个待处理的转让请求。', 'warning')
            return redirect(url_for('initiate_transfer'))
        
        # 创建转让请求
        transfer_request = TransferRequest(
            from_user_id=current_user.id,
            to_user_id=target_user_id,
            club_id=club_id,
            status='pending'
        )
        db.session.add(transfer_request)
        db.session.commit()
        flash('转让请求已发起，等待目标学生确认。', 'success')
        return redirect(url_for('index'))
    
    return render_template('initiate_transfer.html', form=form)

@app.route('/confirm_transfer', methods=['GET', 'POST'])
@login_required
def confirm_transfer():
    if current_user.is_admin():
        flash('管理员无法确认转让请求。', 'warning')
        return redirect(url_for('index'))
    
    form = ConfirmTransferForm()
    
    # 获取当前用户收到的待确认转让请求
    pending_transfers = TransferRequest.query.filter_by(to_user_id=current_user.id, status='pending').all()
    
    form.transfer_id.choices = [(transfer.id, f"来自 {transfer.from_user.username} 的 {transfer.club.name} 转让") for transfer in pending_transfers]
    
    if not pending_transfers:
        flash('没有待确认的转让请求。', 'info')
        return redirect(url_for('index'))
    
    if form.validate_on_submit():
        transfer_id = form.transfer_id.data
        action = form.action.data
        
        transfer = TransferRequest.query.get_or_404(transfer_id)
        
        if transfer.to_user_id != current_user.id:
            flash('您无权确认此转让请求。', 'danger')
            return redirect(url_for('confirm_transfer'))
        
        if action == 'confirm':
            # 检查目标学生是否已加入两个社团
            target_memberships = Membership.query.filter_by(user_id=current_user.id).count()
            if target_memberships >= 2:
                flash('您已加入两个社团，无法接收更多名额。', 'warning')
                transfer.status = 'rejected'
                db.session.commit()
                return redirect(url_for('confirm_transfer'))
            
            # 移除转让者的社团会员关系
            from_membership = Membership.query.filter_by(user_id=transfer.from_user_id, club_id=transfer.club_id).first()
            if from_membership:
                db.session.delete(from_membership)
            
            # 添加接收者的社团会员关系
            new_membership = Membership(user_id=current_user.id, club_id=transfer.club_id)
            db.session.add(new_membership)
            
            # 更新转让请求状态
            transfer.status = 'confirmed'
            db.session.commit()
            flash('转让请求已确认，社团名额已成功转让。', 'success')
        elif action == 'reject':
            transfer.status = 'rejected'
            db.session.commit()
            flash('转让请求已拒绝。', 'info')
        
        return redirect(url_for('confirm_transfer'))
    
    return render_template('confirm_transfer.html', form=form)

def create_tables():
    with app.app_context():
        db.create_all()

def create_admin():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

@app.after_request
def add_header(response):
    # 保留安全头
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # 对图片文件设置缓存控制
    if response.mimetype.startswith('image/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

@app.context_processor
def utility_processor():
    return {
        'timestamp': int(time.time())
    }

# 启动应用
if __name__ == '__main__':
    with app.app_context():
        create_tables()  # 创建数据库表
        create_admin()   # 创建管理员账户
    app.run(debug=True, host='0.0.0.0', port=5000)
