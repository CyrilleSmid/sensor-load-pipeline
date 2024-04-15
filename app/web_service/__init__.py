from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from web_service.simulation_management import send_user_info_to_client_manager
import logging as log
log.basicConfig(level=log.INFO)

app = Flask(__name__,template_folder='./frontend/templates', static_folder='./frontend/static')
app.config['SECRET_KEY'] = '1c47a3803abcb25f4b87b078afcf09f6'
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///../web_service/databases/sqlite.db"

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# client = docker.from_env()

from web_service.models import User
with app.app_context():
    db.create_all()
    # table_names = db.metadata.tables.keys()
    # print(table_names)
    users = User.query.all()
    log.info(f"Starting simulations for users: {[user.id for user in users]}")
    for user in users:
        send_user_info_to_client_manager(user.id, None)
        

from web_service import routes