from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import uuid
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///property.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5006")

db = SQLAlchemy(app)

# Ensure uploads folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# Models
class Property(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    price_eur = db.Column(db.Float, nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # apartment|house|land|commercial
    rooms = db.Column(db.Integer, nullable=True)
    area_m2 = db.Column(db.Float, nullable=True)
    is_for_sale = db.Column(db.Boolean, default=True, nullable=False)
    is_for_rent = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    photos = db.relationship("Photo", backref="property", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "city": self.city,
            "address": self.address,
            "price_eur": self.price_eur,
            "property_type": self.property_type,
            "rooms": self.rooms,
            "area_m2": self.area_m2,
            "is_for_sale": self.is_for_sale,
            "is_for_rent": self.is_for_rent,
            "created_at": self.created_at.isoformat(),
            "photos": [photo.to_dict() for photo in self.photos]
        }


class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat()
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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# Routes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "property-service"}), 200


@app.route("/properties", methods=["GET"])
def get_properties():
    """Get all properties with optional filters"""
    city = request.args.get("city")
    property_type = request.args.get("property_type")
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    
    query = Property.query
    
    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if property_type:
        query = query.filter_by(property_type=property_type)
    if min_price:
        query = query.filter(Property.price_eur >= min_price)
    if max_price:
        query = query.filter(Property.price_eur <= max_price)
    
    properties = query.order_by(Property.created_at.desc()).all()
    return jsonify([prop.to_dict() for prop in properties]), 200


@app.route("/properties/<int:property_id>", methods=["GET"])
def get_property(property_id: int):
    """Get single property by ID"""
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    return jsonify(prop.to_dict()), 200


@app.route("/properties", methods=["POST"])
def create_property():
    """Create new property (agent only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.form
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    city = data.get("city", "").strip()
    address = data.get("address", "").strip()
    price_eur = float(data.get("price_eur", 0) or 0)
    property_type = data.get("property_type", "apartment")
    rooms = int(data.get("rooms", 0) or 0)
    area_m2 = float(data.get("area_m2", 0) or 0)
    is_for_sale = data.get("is_for_sale") == "true"
    is_for_rent = data.get("is_for_rent") == "true"
    
    if not title or not city or not address or price_eur <= 0:
        return jsonify({"error": "Missing required fields"}), 400
    
    prop = Property(
        title=title,
        description=description or None,
        city=city,
        address=address,
        price_eur=price_eur,
        property_type=property_type,
        rooms=rooms or None,
        area_m2=area_m2 or None,
        is_for_sale=is_for_sale,
        is_for_rent=is_for_rent
    )
    db.session.add(prop)
    db.session.flush()
    
    # Handle photo uploads
    if 'photos' in request.files:
        files = request.files.getlist('photos')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                file.save(filepath)
                
                photo = Photo(property_id=prop.id, file_path=unique_filename)
                db.session.add(photo)
    
    db.session.commit()
    
    # Send notification about new property to all users
    try:
        sale_rent = []
        if prop.is_for_sale:
            sale_rent.append("продажа")
        if prop.is_for_rent:
            sale_rent.append("аренда")
        
        notification_message = f"🏠 Новый объект! {prop.title} в {prop.city}, {prop.price_eur}€ ({', '.join(sale_rent)})"
        requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json={
                "recipient": "all-users@agency.com",
                "channel": "push",
                "message": notification_message
            },
            timeout=3
        )
    except Exception as e:
        print(f"Failed to send new property notification: {e}")
    
    return jsonify(prop.to_dict()), 201


@app.route("/properties/<int:property_id>", methods=["PUT"])
def update_property(property_id: int):
    """Update property (agent only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    
    data = request.get_json()
    
    if "title" in data:
        prop.title = data["title"]
    if "description" in data:
        prop.description = data["description"]
    if "city" in data:
        prop.city = data["city"]
    if "address" in data:
        prop.address = data["address"]
    if "price_eur" in data:
        prop.price_eur = float(data["price_eur"])
    if "property_type" in data:
        prop.property_type = data["property_type"]
    if "rooms" in data:
        prop.rooms = int(data["rooms"]) if data["rooms"] else None
    if "area_m2" in data:
        prop.area_m2 = float(data["area_m2"]) if data["area_m2"] else None
    if "is_for_sale" in data:
        prop.is_for_sale = data["is_for_sale"]
    if "is_for_rent" in data:
        prop.is_for_rent = data["is_for_rent"]
    
    db.session.commit()
    return jsonify(prop.to_dict()), 200


@app.route("/properties/<int:property_id>", methods=["DELETE"])
def delete_property(property_id: int):
    """Delete property (agent only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user or user.get("role") != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    prop = db.session.get(Property, property_id)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    
    # Delete associated photos from filesystem
    for photo in prop.photos:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], photo.file_path)
        if os.path.exists(filepath):
            os.remove(filepath)
    
    db.session.delete(prop)
    db.session.commit()
    return jsonify({"message": "Property deleted"}), 200


@app.route("/uploads/<filename>", methods=["GET"])
def get_upload(filename):
    """Serve uploaded photo"""
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    return jsonify({"error": "File not found"}), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=True)
