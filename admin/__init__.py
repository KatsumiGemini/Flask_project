from flask import Flask
from .extensions import db, login_manager, bcrypt,mail
from dotenv import load_dotenv
import os

# Load .env file FIRST
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Secret Key from .env
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_NAME = os.getenv("DB_NAME")

    user = 'testman'
    password = 'Jhayg3309]]:P' 
    mysql_url = 'vultr-prod-85f8d360-5bbf-4d05-ad2d-01cc47768728-vultr-prod-995c.vultrdb.com'
    port_num = '16751' 

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{user}:{password}@{mysql_url}:{port_num}/sample_crud'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Reset password requesnt mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'nakanohirumo@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ytfb jipo ljou qeqm'
    app.config['MAIL_DEFAULT_SENDER'] = 'nakanohirumo@gmail.com'

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    login_manager.login_view = 'second.login'

    # Register blueprint
    from .second import second
    app.register_blueprint(second, url_prefix="/admin")

    # User loader
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
