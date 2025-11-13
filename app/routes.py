from datetime import datetime
import os
import uuid

from flask import flash, redirect, render_template, request, url_for, send_from_directory, abort, send_file
from flask_login import current_user, login_required, login_user, logout_user, AnonymousUserMixin
from . import app, db

# --- Change inquiry status (agent only) ---
@app.route("/inquiry/<int:inquiry_id>/status", methods=["POST"])
@login_required
def change_inquiry_status(inquiry_id):
	if current_user.role != "agent":
		return redirect(url_for("index"))
	inquiry = Inquiry.query.get_or_404(inquiry_id)
	new_status = request.form.get("status")
	if new_status in ["new", "in_progress", "done", "rejected"]:
		inquiry.status = new_status
		db.session.commit()
		flash("Статус заявки обновлен!", "success")
	return redirect(url_for("all_inquiries"))
from werkzeug.utils import secure_filename

from . import app, db
from .models import (Appointment, Client, Comment, Inquiry, Photo, Project,
				   ProjectMember, Property, Task, User)

# --- Edit property (agent only) ---
@app.route("/properties/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
def edit_property(property_id: int):
	if current_user.role != "agent":
		return redirect(url_for("index"))
	obj = Property.query.get_or_404(property_id)
	if request.method == "POST":
		obj.title = request.form.get("title", obj.title).strip()
		obj.description = request.form.get("description", obj.description).strip()
		obj.city = request.form.get("city", obj.city).strip()
		obj.address = request.form.get("address", obj.address).strip()
		obj.price_eur = float(request.form.get("price_eur", obj.price_eur) or obj.price_eur)
		obj.property_type = request.form.get("property_type", obj.property_type)
		obj.rooms = int(request.form.get("rooms", obj.rooms) or obj.rooms)
		obj.area_m2 = float(request.form.get("area_m2", obj.area_m2) or obj.area_m2)
		obj.is_for_sale = request.form.get("is_for_sale") == "on"
		obj.is_for_rent = request.form.get("is_for_rent") == "on"
		db.session.commit()
		flash("Объект обновлен!", "success")
		return redirect(url_for("property_detail", property_id=obj.id))
	return render_template("property_edit.html", p=obj)

# --- Inquiries views by role ---
@app.route("/my_inquiries")
@login_required
def my_inquiries():
	# Только для клиента
	if current_user.role != "user":
		return redirect(url_for("index"))
	client = Client.query.filter_by(email=current_user.email).first()
	inquiries = client.inquiries if client else []
	return render_template("my_inquiries.html", inquiries=inquiries)

@app.route("/all_inquiries")
@login_required
def all_inquiries():
	# Только для агента
	if current_user.role != "agent":
		return redirect(url_for("index"))
	inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).all()
	return render_template("all_inquiries.html", inquiries=inquiries)

@app.route("/")
def index():
	if current_user.is_authenticated:
		# Домашняя страница: список объектов недвижимости
		properties = Property.query.order_by(Property.created_at.desc()).all()
		return render_template("properties.html", properties=properties)
	return render_template("index.html", tasks=[])  # гостевая страница


# --- Properties CRUD ---

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@app.route("/uploads/<filename>")
def uploaded_file(filename):
	import mimetypes
	
	# Определяем абсолютный путь к папке uploads
	upload_folder = os.path.abspath(app.config['UPLOAD_FOLDER'])
	file_path = os.path.join(upload_folder, filename)
	
	# Проверяем, существует ли файл
	if os.path.exists(file_path):
		mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
		return send_file(file_path, mimetype=mime)
	else:
		# Если файл не найден, возвращаем 404
		abort(404)


@app.route("/properties/new", methods=["GET", "POST"])
@login_required
def new_property():
	if current_user.role != "agent":
		return redirect(url_for("index"))
	if request.method == "POST":
		title = request.form.get("title", "").strip()
		description = request.form.get("description", "").strip()
		city = request.form.get("city", "").strip()
		address = request.form.get("address", "").strip()
		price_eur = float(request.form.get("price_eur", 0) or 0)
		property_type = request.form.get("property_type", "apartment")
		rooms = int(request.form.get("rooms", 0) or 0)
		area_m2 = float(request.form.get("area_m2", 0) or 0)
		is_for_sale = request.form.get("is_for_sale") == "on"
		is_for_rent = request.form.get("is_for_rent") == "on"
		if title and city and address and price_eur > 0:
			obj = Property(title=title, description=description or None, city=city,
						address=address, price_eur=price_eur, property_type=property_type,
						rooms=rooms or None, area_m2=area_m2 or None,
						is_for_sale=is_for_sale, is_for_rent=is_for_rent)
			db.session.add(obj)
			db.session.flush()  # Get the ID
			# Ensure uploads folder exists
			upload_folder = app.config['UPLOAD_FOLDER']
			if not os.path.exists(upload_folder):
				os.makedirs(upload_folder)
			# Handle photo uploads
			if 'photos' in request.files:
				files = request.files.getlist('photos')
				for file in files:
					if file and file.filename and allowed_file(file.filename):
						filename = secure_filename(file.filename)
						unique_filename = f"{uuid.uuid4()}_{filename}"
						filepath = os.path.join(upload_folder, unique_filename)
						file.save(filepath)
						# Сохраняем только имя файла для корректного отображения
						photo = Photo(property_id=obj.id, file_path=unique_filename)
						db.session.add(photo)
			db.session.commit()
			return redirect(url_for("index"))
	return render_template("property_form.html")


@app.route("/properties/<int:property_id>")
def property_detail(property_id: int):
	obj = Property.query.get_or_404(property_id)
	return render_template("property_detail.html", p=obj)


@app.route("/properties/<int:property_id>/delete", methods=["POST"]) 
@login_required
def property_delete(property_id: int):
	obj = Property.query.get_or_404(property_id)
	db.session.delete(obj)
	db.session.commit()
	return redirect(url_for("index"))


# --- Inquiries and Appointments ---

@app.route("/properties/<int:property_id>/inquiry", methods=["POST"])
def create_inquiry(property_id: int):
	property_obj = Property.query.get_or_404(property_id)
	name = request.form.get("name", "").strip()
	email = request.form.get("email", "").strip()
	phone = request.form.get("phone", "").strip()
	message = request.form.get("message", "").strip()
	
	if name and (email or phone):
		# Try to find existing client
		client = None
		if email:
			client = Client.query.filter_by(email=email).first()
		if not client and phone:
			client = Client.query.filter_by(phone=phone).first()
		
		# Create client if not found
		if not client:
			client = Client(name=name, email=email or None, phone=phone or None)
			db.session.add(client)
			db.session.flush()
		
		# Create inquiry
		inquiry = Inquiry(property_id=property_id, client_id=client.id,
						name=name, email=email or None, phone=phone or None,
						message=message or None)
		db.session.add(inquiry)
		db.session.commit()
		flash("Заявка отправлена! Мы свяжемся с вами в ближайшее время.", "success")
	
	return redirect(url_for("property_detail", property_id=property_id))


@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
	if request.method == "POST":
		property_id = int(request.form.get("property_id", 0))
		client_name = request.form.get("client_name", "").strip()
		client_email = request.form.get("client_email", "").strip()
		client_phone = request.form.get("client_phone", "").strip()
		scheduled_at_str = request.form.get("scheduled_at", "").strip()
		note = request.form.get("note", "").strip()
		
		if property_id and client_name and scheduled_at_str:
			try:
				scheduled_at = datetime.fromisoformat(scheduled_at_str)
				
				# Find or create client
				client = Client.query.filter_by(email=client_email).first()
				if not client:
					client = Client(name=client_name, email=client_email or None, phone=client_phone or None)
					db.session.add(client)
					db.session.flush()
				
				appointment = Appointment(property_id=property_id, client_id=client.id,
										scheduled_at=scheduled_at, note=note or None)
				db.session.add(appointment)
				db.session.commit()
				flash("Показ запланирован!", "success")
			except ValueError:
				flash("Неверный формат даты", "error")
	
	# Get all appointments
	appointments_list = Appointment.query.order_by(Appointment.scheduled_at).all()
	properties = Property.query.all()
	return render_template("appointments.html", appointments=appointments_list, properties=properties)


@app.route("/register", methods=["GET", "POST"])
def register():
	if request.method == "POST":
		email = request.form.get("email", "").lower().strip()
		password = request.form.get("password", "")
		if not email or not password:
			flash("Заполните email и пароль", "error")
			return render_template("register.html")
		if User.query.filter_by(email=email).first():
			flash("Пользователь уже существует", "error")
			return render_template("register.html")
		
		# Использовать простой хеш вместо bcrypt
		import hashlib
		password_hash = hashlib.sha256(password.encode()).hexdigest()
		
		try:
			user = User(email=email, password_hash=password_hash)
			db.session.add(user)
			db.session.commit()
			login_user(user)
			return redirect(url_for("index"))
		except Exception as e:
			flash(f"Ошибка при создании пользователя: {str(e)}", "error")
			return render_template("register.html")
	return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		email = request.form.get("email", "").lower().strip()
		password = request.form.get("password", "")
		user = User.query.filter_by(email=email).first()
		
		# Использовать простой хеш вместо bcrypt
		import hashlib
		password_hash = hashlib.sha256(password.encode()).hexdigest()
		
		try:
			if user and user.password_hash == password_hash:
				login_user(user)
				return redirect(url_for("index"))
			flash("Неверные учетные данные", "error")
		except Exception as e:
			flash(f"Ошибка при входе: {str(e)}", "error")
	return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))


@app.route("/projects", methods=["POST"])
@login_required
def create_project():
	name = request.form.get("name", "").strip()
	if name:
		project = Project(name=name, owner_id=current_user.id)
		db.session.add(project)
		db.session.commit()
	return redirect(url_for("index"))


@app.route("/projects/<int:project_id>")
@login_required
def view_project(project_id: int):
	project = Project.query.get_or_404(project_id)
	tasks = Task.query.filter_by(project_id=project.id).order_by(Task.created_at.desc()).all()
	return render_template("project_detail.html", project=project, tasks=tasks)


@app.route("/projects/<int:project_id>/tasks", methods=["POST"]) 
@login_required
def create_task(project_id: int):
	project = Project.query.get_or_404(project_id)
	title = request.form.get("title", "").strip()
	description = request.form.get("description", "").strip()
	status = request.form.get("status", "todo")
	priority = int(request.form.get("priority", 2))
	due_date_raw = request.form.get("due_date", "").strip()
	due_date = datetime.fromisoformat(due_date_raw) if due_date_raw else None
	if title:
		task = Task(project_id=project.id, title=title, description=description or None,
				 status=status, priority=priority, due_date=due_date)
		db.session.add(task)
		db.session.commit()
	return redirect(url_for("view_project", project_id=project.id))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"]) 
@login_required
def toggle_task(task_id: int):
	task = Task.query.get_or_404(task_id)
	task.is_done = not task.is_done
	db.session.commit()
	return redirect(request.referrer or url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"]) 
@login_required
def delete_task(task_id: int):
	task = Task.query.get_or_404(task_id)
	project_id = task.project_id
	db.session.delete(task)
	db.session.commit()
	return redirect(url_for("view_project", project_id=project_id))


