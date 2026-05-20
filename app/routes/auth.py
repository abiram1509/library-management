from app import limiter
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import User, UserSettings
import bcrypt



auth = Blueprint('auth', __name__)


@auth.route('/')
def home():
    return redirect(url_for('auth.login'))


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            session['role']    = user.role
            session['name']    = user.name
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        password = request.form['password']

        # check if email already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered', 'error')
            return redirect(url_for('auth.signup'))

        # hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # create user
        new_user = User(
            name          = name,
            email         = email,
            password_hash = hashed.decode('utf-8')
        )
        db.session.add(new_user)
        db.session.commit()

        # create default settings for user
        settings = UserSettings(user_id=new_user.id)
        db.session.add(settings)
        db.session.commit()

        flash('Account created! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))