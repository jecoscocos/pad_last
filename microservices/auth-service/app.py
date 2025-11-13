from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import hashlib
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///auth.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5006")

db = SQLAlchemy(app)


# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)  # user|agent|admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat()
        }


# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


def verify_token(token: str):
    try:
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# Routes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "auth-service"}), 200


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    role = data.get("role", "user")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 409
    
    password_hash = hash_password(password)
    user = User(email=email, password_hash=password_hash, role=role)
    db.session.add(user)
    db.session.commit()
    
    # Send welcome notification
    try:
        role_names = {
            "user": "пользователь",
            "agent": "агент",
            "admin": "администратор"
        }
        welcome_message = f"👋 Добро пожаловать в агентство недвижимости! Вы зарегистрированы как {role_names.get(role, role)}"
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json={
                "recipient": email,
                "channel": "push",
                "message": welcome_message
            },
            timeout=3
        )
    except Exception as e:
        print(f"Failed to send welcome notification: {e}")
    
    token = create_token(user.id, user.email, user.role)
    return jsonify({"user": user.to_dict(), "token": token}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    
    user = User.query.filter_by(email=email).first()
    password_hash = hash_password(password)
    
    if not user or user.password_hash != password_hash:
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = create_token(user.id, user.email, user.role)
    return jsonify({"user": user.to_dict(), "token": token}), 200


@app.route("/verify", methods=["POST"])
def verify():
    """Verify JWT token and return user info"""
    data = request.get_json()
    token = data.get("token", "")
    
    if not token:
        return jsonify({"error": "Token required"}), 400
    
    payload = verify_token(token)
    if not payload:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    return jsonify(payload), 200


@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    """Get user by ID (for inter-service communication)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@app.route("/users", methods=["GET"])
def get_users():
    """Get all users (for admin)"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
