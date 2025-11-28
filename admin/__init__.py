from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "5791628bb0b13ce0c676dfde280ba245"

    # Register blueprint
    from .second import second
    app.register_blueprint(second)

    return app
