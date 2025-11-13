from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///logs.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # INFO|WARNING|ERROR|DEBUG
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "service": self.service,
            "level": self.level,
            "message": self.message,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat()
        }


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "logging-service"}), 200


@app.route("/logs", methods=["POST"])
def create_log():
    """Create log entry"""
    data = request.get_json() or {}
    service = data.get("service", "unknown")
    level = data.get("level", "INFO")
    message = data.get("message", "")
    user_id = data.get("user_id")

    if not message:
        return jsonify({"error": "Message required"}), 400

    log = LogEntry(service=service, level=level, message=message, user_id=user_id)
    db.session.add(log)
    db.session.commit()

    return jsonify(log.to_dict()), 201


@app.route("/logs", methods=["GET"])
def get_logs():
    """Get logs (optional filters: service, level, limit)"""
    service = request.args.get("service")
    level = request.args.get("level")
    limit = request.args.get("limit", type=int, default=100)

    query = LogEntry.query
    if service:
        query = query.filter_by(service=service)
    if level:
        query = query.filter_by(level=level)

    logs = query.order_by(LogEntry.created_at.desc()).limit(limit).all()
    return jsonify([log.to_dict() for log in logs]), 200


@app.route("/logs/stats", methods=["GET"])
def get_stats():
    """Get log statistics by level and service"""
    from sqlalchemy import func
    
    by_level = db.session.query(
        LogEntry.level,
        func.count(LogEntry.id).label("count")
    ).group_by(LogEntry.level).all()
    
    by_service = db.session.query(
        LogEntry.service,
        func.count(LogEntry.id).label("count")
    ).group_by(LogEntry.service).all()
    
    return jsonify({
        "by_level": {level: count for level, count in by_level},
        "by_service": {service: count for service, count in by_service}
    }), 200


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5011))
    app.run(host="0.0.0.0", port=port, debug=True)
