from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import requests
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///payment.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5006")

db = SQLAlchemy(app)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default="EUR", nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)  # pending|success|failed
    property_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "transaction_id": self.transaction_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "property_id": self.property_id,
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


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "payment-service"}), 200


@app.route("/transactions", methods=["POST"])
def create_transaction():
    """Create payment transaction"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    amount = data.get("amount")
    currency = data.get("currency", "EUR")
    property_id = data.get("property_id")

    if not amount or amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400

    transaction_id = str(uuid.uuid4())
    txn = Transaction(
        transaction_id=transaction_id,
        user_id=user["user_id"],
        amount=amount,
        currency=currency,
        property_id=property_id,
        status="success"  # Mock: always success
    )
    db.session.add(txn)
    db.session.commit()
    
    # Send notification to agents
    try:
        property_info = f"объект #{property_id}" if property_id else "счёт"
        notification_message = f"💰 Новый платёж: {amount} {currency} от пользователя #{user['user_id']} за {property_info}"
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json={
                "recipient": "agents@agency.com",
                "channel": "push",
                "message": notification_message
            },
            timeout=3
        )
    except Exception as e:
        print(f"Failed to send payment notification: {e}")

    return jsonify(txn.to_dict()), 201


@app.route("/transactions", methods=["GET"])
def list_transactions():
    """List transactions (user sees own, agent sees all)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user.get("role") == "agent":
        txns = Transaction.query.order_by(Transaction.created_at.desc()).all()
    else:
        txns = Transaction.query.filter_by(user_id=user["user_id"]).order_by(Transaction.created_at.desc()).all()

    return jsonify([t.to_dict() for t in txns]), 200


@app.route("/transactions/<transaction_id>", methods=["GET"])
def get_transaction(transaction_id: str):
    """Get single transaction"""
    txn = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if not txn:
        return jsonify({"error": "Transaction not found"}), 404
    return jsonify(txn.to_dict()), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5009))
    app.run(host="0.0.0.0", port=port, debug=True)
