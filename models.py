from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# 用户模型
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    # __table_args__ = {'extend_existing': True}  # 如果需要临时修正，可以取消注释
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')  # 角色字段：'student' 或 'admin'
    
    memberships = db.relationship('Membership', back_populates='user', cascade="all, delete-orphan")
    sent_transfers = db.relationship('TransferRequest', foreign_keys='TransferRequest.from_user_id', back_populates='from_user')
    received_transfers = db.relationship('TransferRequest', foreign_keys='TransferRequest.to_user_id', back_populates='to_user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

# 社团模型
class Club(db.Model):
    __tablename__ = 'club'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)  # 添加描述字段
    member_limit = db.Column(db.Integer, nullable=False, default=3)  # 添加人数限制字段
    
    memberships = db.relationship('Membership', back_populates='club', cascade="all, delete-orphan")
    transfer_requests = db.relationship('TransferRequest', back_populates='club', cascade="all, delete-orphan")

# 会员关系模型
class Membership(db.Model):
    __tablename__ = 'membership'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', back_populates='memberships')
    club = db.relationship('Club', back_populates='memberships')

    __table_args__ = (db.UniqueConstraint('user_id', 'club_id', name='unique_membership'),)

# 名额转让请求模型
class TransferRequest(db.Model):
    __tablename__ = 'transfer_request'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 状态：pending, confirmed, rejected
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    from_user = db.relationship('User', foreign_keys=[from_user_id], back_populates='sent_transfers')
    to_user = db.relationship('User', foreign_keys=[to_user_id], back_populates='received_transfers')
    club = db.relationship('Club', back_populates='transfer_requests') 