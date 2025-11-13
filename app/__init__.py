from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# Import routes after app/db initialization to avoid circular imports
from . import routes  # noqa: E402,F401


