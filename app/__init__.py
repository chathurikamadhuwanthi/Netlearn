import os
from flask import Flask
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["DATABASE"] = os.path.join(app.instance_path, "netlearn.db")

    from . import db
    db.init_app(app)

    from .main import bp as main_bp
    from .auth import bp as auth_bp
    from .learn import bp as learn_bp
    from .tools import bp as tools_bp
    from .certificate import bp as certificate_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(learn_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(certificate_bp)

    return app