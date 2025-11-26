from flask import Flask
from db import db, init_db
from flask_login import LoginManager
from models import User
import os
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

app.config['SECRET_KEY'] = '0b6442c15d45eeff93f6e9c260c66c677597c82f148cbdc97133f93420c3eef0'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database","database.db")}'

init_db(app)

login_manager = LoginManager()
login_manager.login_view = 'login_page'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

logging.basicConfig(
    filename=os.path.join(basedir, "log","app.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


from routes import *

if __name__ == "__main__":
    app.run(debug=True)