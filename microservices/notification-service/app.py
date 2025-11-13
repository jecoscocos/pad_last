from flask import Flask, request, jsonify
from datetime import datetime
import os
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///notification.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")

db = SQLAlchemy(app)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(255), nullable=False)
    channel = db.Column(db.String(50), nullable=False)  # email|sms|push
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "recipient": self.recipient,
            "channel": self.channel,
            "message": self.message,
            "created_at": self.created_at.isoformat()
        }


def verify_token(token: str):
    try:
        response = requests.post(f"{AUTH_SERVICE_URL}/verify", json={"token": token}, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "notification-service"}), 200

@app.route('/notifications', methods=['POST'])
def create_notification():
    # optional auth (agents can create notifications)
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = verify_token(token) if token else None

    data = request.get_json() or {}
    recipient = data.get('recipient')
    channel = data.get('channel', 'email')
    message = data.get('message')

    if not recipient or not message:
        return jsonify({"error": "recipient and message required"}), 400

    notif = Notification(recipient=recipient, channel=channel, message=message)
    db.session.add(notif)
    db.session.commit()

    # Mock send: in real app integrate with SMTP/SMS provider
    print(f"[notification] send to={recipient} channel={channel} message={message}")

    return jsonify(notif.to_dict()), 201

@app.route('/notifications', methods=['GET'])
def list_notifications():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    print(f"[DEBUG] Token received: {token[:20] if token else 'NONE'}...")
    
    user = verify_token(token)
    print(f"[DEBUG] User verified: {user}")
    
    if not user:
        print(f"[DEBUG] Unauthorized - no user")
        return jsonify({"error": "Unauthorized"}), 401
    
    user_email = user.get('email')
    user_role = user.get('role')
    print(f"[DEBUG] User: {user_email}, Role: {user_role}")
    
    # Agents see all notifications, users see only their own
    if user_role == 'agent':
        items = Notification.query.order_by(Notification.created_at.desc()).all()
    else:
        # Show notifications for this user (by email) and broadcast notifications (agents@, all-users@)
        items = Notification.query.filter(
            (Notification.recipient == user_email) | 
            (Notification.recipient.in_(['agents@agency.com', 'all-users@agency.com']))
        ).order_by(Notification.created_at.desc()).all()
    
    print(f"[DEBUG] Returning {len(items)} notifications")
    return jsonify([i.to_dict() for i in items]), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5006))
    app.run(host='0.0.0.0', port=port, debug=True)
