from flask import render_template, url_for, flash, redirect, request, session, abort
from web_service import app, db, bcrypt
from web_service.forms import RegistrationFormUser, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from web_service.models import User
from datetime import datetime
import docker
import secrets
import os

@app.route('/')
@app.route('/home')
def index():
    return render_template("index.html", title='Home')

@app.route('/about')
def about():
    return render_template("about.html", title='About')

def save_user(form):
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    user = User(email=form.email.data,
                registration_date=datetime.utcnow(),
                password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return user

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationFormUser()
    if form.validate_on_submit():
        user = save_user(form)
        flash(f'User account created for {form.email}!', 'success')
        return redirect(url_for('login'))
    return render_template('register_base.html', title='Register User', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    return render_template('account.html', title='Account', form=form)

@app.route("/dashboard", methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

