from app import app, db
from models import User

def check_and_fix_user_roles():
    with app.app_context():
        # 检查所有用户
        users = User.query.all()
        for user in User.query.all():
            print(f"User: {user.username}, Current Role: {user.role}")
            
            # 确保admin用户有正确的角色
            if user.username == 'admin' and user.role != 'admin':
                user.role = 'admin'
                print(f"Fixed admin role for user: {user.username}")
            
            # 确保学生用户有正确的角色
            if user.username in ['小黄同学', '小刘同学', '小陆同学'] and user.role != 'student':
                user.role = 'student'
                print(f"Fixed student role for user: {user.username}")
        
        # 提交更改
        db.session.commit()
        print("User roles check completed")

if __name__ == "__main__":
    check_and_fix_user_roles() 