from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///inquiry.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")
PROPERTY_SERVICE_URL = os.environ.get("PROPERTY_SERVICE_URL", "http://localhost:5002")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5006")

db = SQLAlchemy(app)


# Models
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    inquiries = db.relationship("Inquiry", backref="client", lazy=True)
    appointments = db.relationship("Appointment", backref="client", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat()
        }


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)  # Reference to property in property-service
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='new', nullable=False)  # new|in_progress|done|rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "client_id": self.client_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, nullable=False)  # Reference to property in property-service
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "client_id": self.client_id,
            "scheduled_at": self.scheduled_at.isoformat(),
            "note": self.note,
            "created_at": self.created_at.isoformat(),
            "client": self.client.to_dict() if self.client else None
        }


# Helper functions
def verify_token(token: str):
    """Verify token with auth service"""
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/verify",
            json={"token": token},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


# Routes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "inquiry-service"}), 200


# Client routes
@app.route("/clients", methods=["GET"])
def get_clients():
    """Get all clients (agent only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    clients = Client.query.all()
    return jsonify([client.to_dict() for client in clients]), 200


@app.route("/clients/<int:client_id>", methods=["GET"])
def get_client(client_id: int):
    """Get client by ID"""
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client.to_dict()), 200


# Inquiry routes
@app.route("/inquiries", methods=["POST"])
def create_inquiry():
    """Create new inquiry (public endpoint, but links to user if authenticated)"""
    data = request.get_json()
    property_id = data.get("property_id")
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()
    
    # Check if user is authenticated
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token) if token else None
    
    # If authenticated, use user's email
    if user and not email:
        email = user.get("email", "")
    
    if not property_id or not name or (not email and not phone):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Verify property exists
    try:
        prop_response = requests.get(f"{PROPERTY_SERVICE_URL}/properties/{property_id}", timeout=5)
        if prop_response.status_code != 200:
            return jsonify({"error": "Property not found"}), 404
    except:
        return jsonify({"error": "Could not verify property"}), 500
    
    # Find or create client
    client = None
    if email:
        client = Client.query.filter_by(email=email).first()
    if not client and phone:
        client = Client.query.filter_by(phone=phone).first()
    
    if not client:
        client = Client(name=name, email=email or None, phone=phone or None)
        db.session.add(client)
        db.session.flush()
    
    # Create inquiry
    inquiry = Inquiry(
        property_id=property_id,
        client_id=client.id,
        name=name,
        email=email or None,
        phone=phone or None,
        message=message or None
    )
    db.session.add(inquiry)
    db.session.commit()
    
    # Send notification to agents
    try:
        notification_message = f"Новая заявка #{inquiry.id} от {name} ({email or phone}) на объект #{property_id}"
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json={
                "recipient": "agents@agency.com",  # В реальности можно получить email всех агентов
                "channel": "email",
                "message": notification_message
            },
            timeout=3
        )
    except Exception as e:
        print(f"Failed to send notification: {e}")
    
    return jsonify(inquiry.to_dict()), 201


@app.route("/inquiries", methods=["GET"])
def get_inquiries():
    """Get all inquiries or filter by client (agent sees all, user sees their own)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    if user.get("role") == "agent":
        # Agent sees all inquiries
        inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
    else:
        # User sees only their own inquiries
        client = Client.query.filter_by(email=user.get("email")).first()
        if not client:
            return jsonify([]), 200
        inquiries = client.inquiries
    
    return jsonify([inquiry.to_dict() for inquiry in inquiries]), 200


@app.route("/inquiries/<int:inquiry_id>", methods=["GET"])
def get_inquiry(inquiry_id: int):
    """Get single inquiry"""
    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        return jsonify({"error": "Inquiry not found"}), 404
    return jsonify(inquiry.to_dict()), 200


@app.route("/inquiries/<int:inquiry_id>/status", methods=["PUT"])
def update_inquiry_status(inquiry_id: int):
    """Update inquiry status (agent only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        return jsonify({"error": "Inquiry not found"}), 404
    
    data = request.get_json()
    new_status = data.get("status")
    
    if new_status not in ["new", "in_progress", "done", "rejected"]:
        return jsonify({"error": "Invalid status"}), 400
    
    old_status = inquiry.status
    inquiry.status = new_status
    db.session.commit()
    
    # Send notification to user about status change
    if inquiry.email and old_status != new_status:
        try:
            status_names = {
                "new": "новая",
                "in_progress": "в обработке",
                "done": "выполнена",
                "rejected": "отклонена"
            }
            notification_message = f"📋 Статус вашей заявки #{inquiry_id} изменён: {status_names.get(old_status, old_status)} → {status_names.get(new_status, new_status)}"
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json={
                    "recipient": inquiry.email,
                    "channel": "push",
                    "message": notification_message
                },
                timeout=3
            )
        except Exception as e:
            print(f"Failed to send status notification: {e}")
    
    return jsonify(inquiry.to_dict()), 200


@app.route("/inquiries/<int:inquiry_id>", methods=["DELETE"])
def delete_inquiry(inquiry_id: int):
    """Delete inquiry (user can delete their own, agent can delete any)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    inquiry = Inquiry.query.get(inquiry_id)
    if not inquiry:
        return jsonify({"error": "Inquiry not found"}), 404
    
    # Users can only delete their own inquiries, agents can delete any
    if user.get("role") != "agent":
        # Check if inquiry belongs to user
        if inquiry.email != user.get("email"):
            return jsonify({"error": "You can only delete your own inquiries"}), 403
    
    # Save inquiry data before deletion for notifications
    inquiry_email = inquiry.email
    inquiry_id_str = inquiry_id
    
    db.session.delete(inquiry)
    db.session.commit()
    
    # Send notifications about deletion
    try:
        actor_email = user.get("email")
        if user.get("role") == "agent":
            # Notify the inquiry owner (if present)
            if inquiry_email:
                user_message = f"🗑️ Ваша заявка #{inquiry_id_str} была удалена сотрудником агентства ({actor_email})."
                requests.post(
                    f"{NOTIFICATION_SERVICE_URL}/notifications",
                    json={
                        "recipient": inquiry_email,
                        "channel": "push",
                        "message": user_message
                    },
                    timeout=3
                )

            # Notify agents about the deletion
            agent_message = f"🗑️ Заявка #{inquiry_id_str} удалена агентом {actor_email}."
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json={
                    "recipient": "agents@agency.com",
                    "channel": "push",
                    "message": agent_message
                },
                timeout=3
            )
        else:
            # User deleted their own inquiry — confirm to user and notify agents
            if inquiry_email:
                confirm_message = f"✅ Ваша заявка #{inquiry_id_str} успешно удалена."
                requests.post(
                    f"{NOTIFICATION_SERVICE_URL}/notifications",
                    json={
                        "recipient": inquiry_email,
                        "channel": "push",
                        "message": confirm_message
                    },
                    timeout=3
                )

            agent_message = f"🗑️ Пользователь {actor_email} удалил свою заявку #{inquiry_id_str}."
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json={
                    "recipient": "agents@agency.com",
                    "channel": "push",
                    "message": agent_message
                },
                timeout=3
            )
    except Exception as e:
        print(f"Failed to send deletion notification: {e}")

    return jsonify({"message": "Inquiry deleted successfully"}), 200


# Appointment routes
@app.route("/appointments", methods=["POST"])
def create_appointment():
    """Create new appointment"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    property_id = data.get("property_id")
    client_name = data.get("client_name", "").strip()
    client_email = data.get("client_email", "").strip()
    client_phone = data.get("client_phone", "").strip()
    scheduled_at_str = data.get("scheduled_at", "").strip()
    note = data.get("note", "").strip()
    
    if not property_id or not client_name or not scheduled_at_str:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        scheduled_at = datetime.fromisoformat(scheduled_at_str)
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400
    
    # Verify property exists
    try:
        prop_response = requests.get(f"{PROPERTY_SERVICE_URL}/properties/{property_id}", timeout=5)
        if prop_response.status_code != 200:
            return jsonify({"error": "Property not found"}), 404
    except:
        return jsonify({"error": "Could not verify property"}), 500
    
    # Find or create client
    client = Client.query.filter_by(email=client_email).first()
    if not client:
        client = Client(name=client_name, email=client_email or None, phone=client_phone or None)
        db.session.add(client)
        db.session.flush()
    
    # Create appointment
    appointment = Appointment(
        property_id=property_id,
        client_id=client.id,
        scheduled_at=scheduled_at,
        note=note or None
    )
    db.session.add(appointment)
    db.session.commit()
    
    # Send notifications
    try:
        date_str = scheduled_at.strftime('%d.%m.%Y %H:%M')
        
        # Notification to client
        if client_email:
            client_message = f"📅 Встреча подтверждена! Объект #{property_id}, дата: {date_str}"
            requests.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json={
                    "recipient": client_email,
                    "channel": "push",
                    "message": client_message
                },
                timeout=3
            )
        
        # Notification to agents
        agent_message = f"📅 Новая встреча: {client_name} ({client_email or client_phone}), объект #{property_id}, {date_str}"
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json={
                "recipient": "agents@agency.com",
                "channel": "push",
                "message": agent_message
            },
            timeout=3
        )
    except Exception as e:
        print(f"Failed to send appointment notifications: {e}")
    
    return jsonify(appointment.to_dict()), 201


@app.route("/appointments", methods=["GET"])
def get_appointments():
    """Get all appointments"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    appointments = Appointment.query.order_by(Appointment.scheduled_at).all()
    return jsonify([appointment.to_dict() for appointment in appointments]), 200


@app.route("/appointments/<int:appointment_id>", methods=["GET"])
def get_appointment(appointment_id: int):
    """Get single appointment"""
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    return jsonify(appointment.to_dict()), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5003))
    app.run(host="0.0.0.0", port=port, debug=True)
