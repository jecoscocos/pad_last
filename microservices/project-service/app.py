from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///project.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")

db = SQLAlchemy(app)


# Models
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)  # User ID from auth-service
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    tasks = db.relationship("Task", backref="project", lazy=True, cascade="all, delete-orphan")
    members = db.relationship("ProjectMember", backref="project", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "tasks": [task.to_dict() for task in self.tasks],
            "members": [member.to_dict() for member in self.members]
        }


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="todo", nullable=False)  # todo|in_progress|done
    priority = db.Column(db.Integer, default=2, nullable=False)  # 1-высокий, 2-средний, 3-низкий
    due_date = db.Column(db.DateTime, nullable=True)
    is_done = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    comments = db.relationship("Comment", backref="task", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_done": self.is_done,
            "created_at": self.created_at.isoformat(),
            "comments": [comment.to_dict() for comment in self.comments]
        }


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # User ID from auth-service
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat()
        }


class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)  # User ID from auth-service
    role = db.Column(db.String(50), default="member", nullable=False)  # owner|member
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
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


# Routes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "project-service"}), 200


# Project routes
@app.route("/projects", methods=["POST"])
def create_project():
    """Create new project"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    name = data.get("name", "").strip()
    
    if not name:
        return jsonify({"error": "Project name required"}), 400
    
    project = Project(name=name, owner_id=user["user_id"])
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict()), 201


@app.route("/projects", methods=["GET"])
def get_projects():
    """Get all projects for current user"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    # Get projects owned by user or where user is a member
    owned_projects = Project.query.filter_by(owner_id=user["user_id"]).all()
    member_projects = Project.query.join(ProjectMember).filter(
        ProjectMember.user_id == user["user_id"]
    ).all()
    
    # Combine and deduplicate
    all_projects = list({p.id: p for p in owned_projects + member_projects}.values())
    
    return jsonify([project.to_dict() for project in all_projects]), 200


@app.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id: int):
    """Get single project"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    return jsonify(project.to_dict()), 200


@app.route("/projects/<int:project_id>", methods=["DELETE"])
def delete_project(project_id: int):
    """Delete project (owner only)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    if project.owner_id != user["user_id"]:
        return jsonify({"error": "Only project owner can delete"}), 403
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({"message": "Project deleted"}), 200


# Task routes
@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
def create_task(project_id: int):
    """Create new task in project"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    project = Project.query.get(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    
    data = request.get_json()
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    status = data.get("status", "todo")
    priority = int(data.get("priority", 2))
    due_date_str = data.get("due_date", "").strip()
    
    if not title:
        return jsonify({"error": "Task title required"}), 400
    
    due_date = None
    if due_date_str:
        try:
            due_date = datetime.fromisoformat(due_date_str)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
    
    task = Task(
        project_id=project_id,
        title=title,
        description=description or None,
        status=status,
        priority=priority,
        due_date=due_date
    )
    db.session.add(task)
    db.session.commit()
    
    return jsonify(task.to_dict()), 201


@app.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int):
    """Get single task"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id: int):
    """Update task"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.get_json()
    
    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "status" in data:
        task.status = data["status"]
    if "priority" in data:
        task.priority = int(data["priority"])
    if "is_done" in data:
        task.is_done = data["is_done"]
    if "due_date" in data:
        if data["due_date"]:
            try:
                task.due_date = datetime.fromisoformat(data["due_date"])
            except ValueError:
                return jsonify({"error": "Invalid date format"}), 400
        else:
            task.due_date = None
    
    db.session.commit()
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id: int):
    """Toggle task done status"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    task.is_done = not task.is_done
    db.session.commit()
    
    return jsonify(task.to_dict()), 200


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id: int):
    """Delete task"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({"message": "Task deleted"}), 200


# Comment routes
@app.route("/tasks/<int:task_id>/comments", methods=["POST"])
def create_comment(task_id: int):
    """Create comment on task"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    data = request.get_json()
    body = data.get("body", "").strip()
    
    if not body:
        return jsonify({"error": "Comment body required"}), 400
    
    comment = Comment(body=body, user_id=user["user_id"], task_id=task_id)
    db.session.add(comment)
    db.session.commit()
    
    return jsonify(comment.to_dict()), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5004))
    app.run(host="0.0.0.0", port=port, debug=True)
