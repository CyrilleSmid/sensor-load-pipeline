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
    model_info = db.relationship("ModelInfo", back_populates="user", uselist=False)

    def __init__(self, email, registration_date, password):
        self.email = email
        self.registration_date = registration_date
        self.password = password
        self.model_info = ModelInfo(self.id)  

    def __repr__(self): 
        return f"{self.id} {self.email} {self.registration_date}"


class ModelInfo(db.Model):
    __tablename__ = "ModelInfo"
    id = db.Column("ModelInfoId", db.Integer().with_variant(db.Integer, "sqlite"), primary_key=True, nullable=False)
    user_id = db.Column("UserId", db.Integer, db.ForeignKey("Users.UserId"), nullable=False, unique=True)
    model_last_train_time = db.Column("ModelLastTrainTime", db.DateTime(25), nullable=True)
    model_train_status = db.Column("ModelTrainStatus", db.String(240), nullable=True)
    user = db.relationship("User", back_populates="model_info")

    def __init__(self, user_id, model_last_train_time=None, model_train_status=None):
        self.user_id = user_id
        self.model_last_train_time = model_last_train_time
        self.model_train_status = model_train_status