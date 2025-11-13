from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///analytics.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Event(db.Model):
    """Analytics event: page view, click, etc."""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)  # page_view, click, search
    resource_id = db.Column(db.Integer, nullable=True)
    user_id = db.Column(db.Integer, nullable=True)
    event_metadata = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "metadata": self.event_metadata,
            "created_at": self.created_at.isoformat()
        }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "analytics-service"}), 200


@app.route("/events", methods=["POST"])
def track_event():
    """Track analytics event"""
    data = request.get_json() or {}
    event_type = data.get("event_type", "unknown")
    resource_id = data.get("resource_id")
    user_id = data.get("user_id")
    event_metadata = data.get("metadata", "")

    event = Event(event_type=event_type, resource_id=resource_id, user_id=user_id, event_metadata=event_metadata)
    db.session.add(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201


@app.route("/events", methods=["GET"])
def get_events():
    """Get analytics events (optional filter by type)"""
    event_type = request.args.get("event_type")
    query = Event.query
    if event_type:
        query = query.filter_by(event_type=event_type)
    events = query.order_by(Event.created_at.desc()).limit(100).all()
    return jsonify([e.to_dict() for e in events]), 200


@app.route("/stats", methods=["GET"])
def get_stats():
    """Enhanced stats with unique users and total counts"""
    from sqlalchemy import func
    
    # Total events
    total_events = Event.query.count()
    
    # Total page views
    total_views = Event.query.filter_by(event_type="page_view").count()
    
    # Unique users
    unique_users = db.session.query(
        func.count(func.distinct(Event.user_id))
    ).filter(Event.user_id.isnot(None)).scalar() or 0
    
    # Events by type
    events_by_type = db.session.query(
        Event.event_type,
        func.count(Event.id).label("count")
    ).group_by(Event.event_type).all()
    
    result = {
        "total_events": total_events,
        "total_views": total_views,
        "unique_users": unique_users,
        "events_by_type": {event_type: count for event_type, count in events_by_type}
    }
    
    return jsonify(result), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5007))
    app.run(host="0.0.0.0", port=port, debug=True)
