from datetime import datetime
from web_service import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = "Users"
    id = db.Column("UserId", db.Integer().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False)
    email = db.Column("Email", db.String(120), nullable=False, unique=True)
    registration_date = db.Column("RegistrationDate", db.DateTime(25), nullable=False, default=datetime.utcnow)
    password = db.Column("Password", db.String(60), nullable=False)
    def __init__(self, email, registration_date, password):   
        # self.user_id = user_id
        self.email = email
        self.registration_date = registration_date
        self.password = password
    def __repr__(self): 
        return f"{self.id} {self.email} {self.registration_date}"