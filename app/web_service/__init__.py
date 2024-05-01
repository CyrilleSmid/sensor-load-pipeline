from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from web_service.simulation_management import send_user_info_to_client_manager
import dash_app.influx_query_manager as query_manager
from flask_apscheduler import APScheduler

from dash_app import create_dash_application

import logging as log
log.basicConfig(level=log.INFO)


app = Flask(__name__,template_folder='./frontend/templates', static_folder='./frontend/static')
app.config['SECRET_KEY'] = '1c47a3803abcb25f4b87b078afcf09f6'
app.config['SQLALCHEMY_DATABASE_URI'] = r"sqlite:///../web_service/databases/sqlite.db"
app.app_context().push()

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

create_dash_application(app)

from web_service.models import User
with app.app_context():    
    db.create_all()
    table_names = db.metadata.tables.keys()
    print(table_names)
    users = User.query.all()
    log.info(f"Starting simulations for users: {[user.id for user in users]}")
    for user in users:
        last_timestamp=query_manager.get_last_available_date(client_id=f'client-{user.id}')
        send_user_info_to_client_manager(user.id, last_timestamp=str(last_timestamp))

from web_service.prediction_module import regular_model_update
INTERVAL_TASK_ID = 'interval-task-id'
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
scheduler.add_job(id=INTERVAL_TASK_ID, func=regular_model_update, trigger='interval', seconds=30, max_instances=1)  

from web_service import routes

