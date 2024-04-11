from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__,template_folder='./frontend/templates',static_folder='./frontend/static')
app.config['SECRET_KEY'] = '1c47a3803abcb25f4b87b078afcf09f6'
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///../web_service/databases/sqlite.db"

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from web_service.models import User
with app.app_context():
    db.create_all()
    # table_names = db.metadata.tables.keys()
    # print(table_names)

from web_service import routes