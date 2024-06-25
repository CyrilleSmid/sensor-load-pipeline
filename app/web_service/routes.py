from flask import render_template, url_for, flash, redirect, request, session, abort, jsonify
from web_service import app, db, bcrypt
from web_service.forms import RegistrationFormUser, LoginForm, UpdateAccountForm
from flask_login import login_user, current_user, logout_user, login_required
from web_service.models import User
from datetime import datetime
from web_service.simulation_management import send_user_info_to_client_manager
import dash_app.influx_query_manager as query_manager
import logging as log
log.basicConfig(level=log.INFO)


@app.route('/')
@app.route('/home')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('building_dashboard'))
    else:
        return redirect(url_for('login'))

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
    
    form_is_ok = False
    if request.method == 'POST':
        if request.form.get('test-mode') == 'locust-test':
            form_is_ok = True
        else:
            form_is_ok = form.validate_on_submit()

    if form_is_ok:
        user = save_user(form)
        
        last_timestamp=query_manager.get_last_available_date(client_id=f'client-{user.id}')
        send_user_info_to_client_manager(user.id, str(last_timestamp))
        
        return redirect(url_for('login'))
    return render_template('register_base.html', title='Register User', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    
    form_is_ok = False
    if request.method == 'POST':
        if request.form.get('test-mode') == 'locust-test':
            form_is_ok = True
        else:
            form_is_ok = form.validate_on_submit()

    if form_is_ok:
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

@app.route("/building_dashboard", methods=['GET'])
@login_required
def building_dashboard():
    return render_template('building_dashboard.html', title='Dashboard')

@app.route("/monitoring_dashboard", methods=['GET'])
@login_required
def monitoring_dashboard():
    return render_template('monitoring_dashboard.html', title='Dashboard')


@app.route('/check_status', methods=['GET'])
@login_required
def check_status():
    if 'model_train_status' not in session:
        session['model_train_status'] = current_user.model_info.model_train_status
    elif session['model_train_status'] != current_user.model_info.model_train_status:
        session['model_train_status'] = current_user.model_info.model_train_status
        log.info(f'New status: {current_user.model_info.model_train_status}')
        return jsonify({'status': current_user.model_info.model_train_status})
    return jsonify({'status': 'unchanged'})
    