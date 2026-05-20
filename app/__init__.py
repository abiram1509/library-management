from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # where to redirect if not logged in
    login_manager.login_view = 'auth.login'

    # register blueprints
    from app.routes.auth import auth
    from app.routes.user import user
    from app.routes.admin import admin
    from app.routes.payment import payment

    app.register_blueprint(auth)
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(payment, url_prefix='/payment')

    return app