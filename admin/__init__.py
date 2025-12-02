from flask import Flask
from .extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    app.secret_key = "5791628bb0b13ce0c676dfde280ba245"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/site'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'second.login'
    
    from .second import second
    app.register_blueprint(second, url_prefix="/admin")
    
    # User loader
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
