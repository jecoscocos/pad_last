from datetime import datetime

from flask_login import UserMixin

from . import db, login_manager


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(255), unique=True, nullable=False, index=True)
	password_hash = db.Column(db.String(255), nullable=False)
	role = db.Column(db.String(50), default="user", nullable=False)  # user|admin
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	projects = db.relationship("Project", backref="owner", lazy=True)
	comments = db.relationship("Comment", backref="author", lazy=True)

	def __repr__(self) -> str:
		return f"<User {self.id} {self.email!r}>"


@login_manager.user_loader
def load_user(user_id: str):
	return db.session.get(User, int(user_id))


class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200), nullable=False)
	owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	tasks = db.relationship("Task", backref="project", lazy=True, cascade="all, delete-orphan")
	members = db.relationship("ProjectMember", backref="project", lazy=True, cascade="all, delete-orphan")

	def __repr__(self) -> str:
		return f"<Project {self.id} {self.name!r}>"


class Task(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
	title = db.Column(db.String(200), nullable=False)
	description = db.Column(db.Text, nullable=True)
	status = db.Column(db.String(50), default="todo", nullable=False)  # todo|in_progress|done
	priority = db.Column(db.Integer, default=2, nullable=False)  # 1-высокий,2-средний,3-низкий
	due_date = db.Column(db.DateTime, nullable=True)
	is_done = db.Column(db.Boolean, default=False, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	comments = db.relationship("Comment", backref="task", lazy=True, cascade="all, delete-orphan")

	def __repr__(self) -> str:
		return f"<Task {self.id} {self.title!r} status={self.status} prio={self.priority}>"


class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.Text, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	task_id = db.Column(db.Integer, db.ForeignKey("task.id"), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	def __repr__(self) -> str:
		return f"<Comment {self.id} task={self.task_id} user={self.user_id}>"


class ProjectMember(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
	role = db.Column(db.String(50), default="member", nullable=False)  # owner|member
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	user = db.relationship("User", backref="memberships")

	def __repr__(self) -> str:
		return f"<ProjectMember proj={self.project_id} user={self.user_id} role={self.role}>"


# --- Real estate domain ---

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
	inquiries = db.relationship("Inquiry", backref="property", lazy=True, cascade="all, delete-orphan")

	def __repr__(self) -> str:
		return f"<Property {self.id} {self.city} {self.price_eur}€>"


class Photo(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
	file_path = db.Column(db.String(255), nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Client(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200), nullable=False)
	email = db.Column(db.String(255), nullable=True)
	phone = db.Column(db.String(50), nullable=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	inquiries = db.relationship("Inquiry", backref="client", lazy=True)
	# appointments = db.relationship("Appointment", backref="client", lazy=True)  # удалено для устранения конфликта


class Inquiry(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
	client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
	name = db.Column(db.String(200), nullable=False)
	email = db.Column(db.String(255), nullable=True)
	phone = db.Column(db.String(50), nullable=True)
	message = db.Column(db.Text, nullable=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	status = db.Column(db.String(50), default='new', nullable=False)  # new|in_progress|done|rejected


class Appointment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	property_id = db.Column(db.Integer, db.ForeignKey("property.id"), nullable=False)
	client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
	scheduled_at = db.Column(db.DateTime, nullable=False)
	note = db.Column(db.Text, nullable=True)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

	property = db.relationship("Property", backref="appointments")
	client = db.relationship("Client", backref="client_appointments")


