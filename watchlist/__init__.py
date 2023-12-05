import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))  # sqlite 数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

db = SQLAlchemy(app)
login_manager = LoginManager(app)


# 用户认证
@login_manager.user_loader
def load_user(user_id):
    from watchlist.models import User
    return User.query.get(int(user_id))


login_manager.login_view = 'login'


@app.context_processor
def inject_user():  # 模板上下文处理函数
    from watchlist.models import User     # 避免循环依赖（A 导入 B，B 导入 A）
    user = User.query.first()
    return dict(user=user)  # 需要返回字典，等同于 return {'user': user}


# 避免循环依赖（A 导入 B，B 导入 A）
from watchlist import errors, views, commands


if __name__ == '__main__':
    app.run()
