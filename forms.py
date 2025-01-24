from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, EqualTo
from models import User

class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=2, max=25)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('用户名已存在。请选择另一个用户名。')

class JoinClubForm(FlaskForm):
    club = SelectField('选择社团', coerce=int, validators=[DataRequired()])
    submit = SubmitField('加入社团')

class LeaveClubForm(FlaskForm):
    clubs = SelectField('选择要退出的社团', coerce=int, validators=[DataRequired()])
    submit = SubmitField('退出社团')

class TransferMembershipForm(FlaskForm):
    current_club = SelectField('当前社团', coerce=int, validators=[DataRequired()])
    target_user = SelectField('目标学生', coerce=int, validators=[DataRequired()])
    submit = SubmitField('转让名额')

    def __init__(self, *args, **kwargs):
        self.current_user_id = kwargs.pop('current_user_id', None)
        super(TransferMembershipForm, self).__init__(*args, **kwargs)

    def validate_target_user(self, field):
        if self.current_user_id and field.data == self.current_user_id:
            raise ValidationError('您不能将名额转让给自己。')

# 新增：添加用户表单
class AddUserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('角色', choices=[('student', '学生'), ('admin', '管理员')], validators=[DataRequired()])
    submit = SubmitField('添加用户')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('用户名已存在。请选择另一个用户名。')

# 新增：删除用户表单
class DeleteUserForm(FlaskForm):
    user = SelectField('选择用户', coerce=int, validators=[DataRequired()])
    submit = SubmitField('删除用户')

class InitiateTransferForm(FlaskForm):
    club = SelectField('选择要转让的社团', coerce=int, validators=[DataRequired()])
    target_user = SelectField('选择目标学生', coerce=int, validators=[DataRequired()])
    submit = SubmitField('发起转让')

class ConfirmTransferForm(FlaskForm):
    transfer_id = SelectField('选择要确认的转让请求', coerce=int, validators=[DataRequired()])
    action = SelectField('操作', choices=[('confirm', '确认'), ('reject', '拒绝')], validators=[DataRequired()])
    submit = SubmitField('提交')

class AddClubForm(FlaskForm):
    name = StringField('社团名称', validators=[DataRequired(), Length(min=1, max=100)])
    description = StringField('社团描述', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('添加社团')

class EditClubForm(FlaskForm):
    name = StringField('社团名称', validators=[DataRequired(), Length(min=1, max=100)])
    description = StringField('社团描述', validators=[DataRequired(), Length(max=255)])
    submit = SubmitField('更新社团')

class EditClubLimitForm(FlaskForm):
    member_limit = IntegerField('人数限制', validators=[DataRequired()])
    submit = SubmitField('更新人数限制') 