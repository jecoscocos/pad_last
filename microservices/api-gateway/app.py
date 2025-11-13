from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session, send_file
from werkzeug.utils import secure_filename
import requests
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

# Microservice URLs
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:5001")
PROPERTY_SERVICE_URL = os.environ.get("PROPERTY_SERVICE_URL", "http://localhost:5002")
INQUIRY_SERVICE_URL = os.environ.get("INQUIRY_SERVICE_URL", "http://localhost:5003")
PROJECT_SERVICE_URL = os.environ.get("PROJECT_SERVICE_URL", "http://localhost:5004")
SEARCH_SERVICE_URL = os.environ.get("SEARCH_SERVICE_URL", "http://localhost:5005")
NOTIFICATION_SERVICE_URL = os.environ.get("NOTIFICATION_SERVICE_URL", "http://localhost:5006")
ANALYTICS_SERVICE_URL = os.environ.get("ANALYTICS_SERVICE_URL", "http://localhost:5007")
REPORTING_SERVICE_URL = os.environ.get("REPORTING_SERVICE_URL", "http://localhost:5008")
PAYMENT_SERVICE_URL = os.environ.get("PAYMENT_SERVICE_URL", "http://localhost:5009")
MEDIA_SERVICE_URL = os.environ.get("MEDIA_SERVICE_URL", "http://localhost:5010")
LOGGING_SERVICE_URL = os.environ.get("LOGGING_SERVICE_URL", "http://localhost:5011")


# User class wrapper
class CurrentUser:
    """Wrapper class for user session data to provide Flask-Login-like interface"""
    def __init__(self, user_data):
        self._data = user_data or {}
    
    @property
    def is_authenticated(self):
        return bool(self._data)
    
    @property
    def email(self):
        return self._data.get("email", "")
    
    @property
    def role(self):
        return self._data.get("role", "user")
    
    @property
    def id(self):
        return self._data.get("id")


# Helper functions
def get_auth_headers():
    """Get authorization headers with JWT token from session"""
    token = session.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def get_current_user():
    """Get current user info from session"""
    user_data = session.get("user")
    return CurrentUser(user_data)


# Template filters
@app.template_filter('is_authenticated')
def is_authenticated_filter(s):
    return session.get("user") is not None


@app.context_processor
def inject_user():
    """Inject current user into all templates"""
    return dict(current_user=get_current_user())


# Routes
@app.route("/")
def index():
    """Home page - list properties"""
    if not session.get("user"):
        return render_template("index.html")
    
    # Получаем параметры поиска
    city = request.args.get("city", "").strip()
    property_type = request.args.get("property_type", "").strip()
    max_price = request.args.get("max_price", "").strip()
    
    # Get all properties
    try:
        response = requests.get(f"{PROPERTY_SERVICE_URL}/properties", timeout=5)
        if response.status_code == 200:
            properties = response.json()
        else:
            properties = []
    except:
        properties = []
    
    # Фильтрация на стороне клиента
    if city:
        properties = [p for p in properties if city.lower() in p.get("city", "").lower()]
    
    if property_type:
        properties = [p for p in properties if p.get("property_type") == property_type]
    
    if max_price:
        try:
            max_price_num = float(max_price)
            properties = [p for p in properties if p.get("price_eur", 0) <= max_price_num]
        except ValueError:
            pass
    
    return render_template("properties.html", properties=properties)


# Auth routes
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/register",
                json={"email": email, "password": password},
                timeout=5
            )
            
            if response.status_code == 201:
                data = response.json()
                session["user"] = data["user"]
                session["token"] = data["token"]
                return redirect(url_for("index"))
            else:
                flash(response.json().get("error", "Registration failed"), "error")
        except Exception as e:
            flash(f"Service error: {str(e)}", "error")
    
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower().strip()
        password = request.form.get("password", "")
        
        try:
            response = requests.post(
                f"{AUTH_SERVICE_URL}/login",
                json={"email": email, "password": password},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                session["user"] = data["user"]
                session["token"] = data["token"]
                return redirect(url_for("index"))
            else:
                flash(response.json().get("error", "Login failed"), "error")
        except Exception as e:
            flash(f"Service error: {str(e)}", "error")
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# Property routes
@app.route("/properties/new", methods=["GET", "POST"])
def new_property():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Unauthorized", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        # Prepare multipart form data
        files = {}
        if 'photos' in request.files:
            files['photos'] = request.files.getlist('photos')
        
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'city': request.form.get('city'),
            'address': request.form.get('address'),
            'price_eur': request.form.get('price_eur'),
            'property_type': request.form.get('property_type'),
            'rooms': request.form.get('rooms'),
            'area_m2': request.form.get('area_m2'),
            'is_for_sale': 'true' if request.form.get('is_for_sale') == 'on' else 'false',
            'is_for_rent': 'true' if request.form.get('is_for_rent') == 'on' else 'false'
        }
        
        try:
            # Prepare files for upload
            files_data = []
            if 'photos' in request.files:
                for file in request.files.getlist('photos'):
                    if file and file.filename:
                        files_data.append(('photos', (file.filename, file.stream, file.content_type)))
            
            response = requests.post(
                f"{PROPERTY_SERVICE_URL}/properties",
                data=data,
                files=files_data if files_data else None,
                headers=get_auth_headers(),
                timeout=10
            )
            
            if response.status_code == 201:
                flash("Property created!", "success")
                return redirect(url_for("index"))
            else:
                flash(response.json().get("error", "Failed to create property"), "error")
        except Exception as e:
            flash(f"Service error: {str(e)}", "error")
    
    return render_template("property_form.html")


@app.route("/properties/<int:property_id>")
def property_detail(property_id: int):
    try:
        response = requests.get(
            f"{PROPERTY_SERVICE_URL}/properties/{property_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            prop = response.json()
            
            # Track property view event
            user = get_current_user()
            if user.is_authenticated:
                try:
                    requests.post(
                        f"{ANALYTICS_SERVICE_URL}/events",
                        json={
                            "event_type": "property_view",
                            "resource_id": property_id,
                            "user_id": user.id,
                            "metadata": f"Просмотр: {prop.get('title', '')}"
                        },
                        timeout=2
                    )
                except:
                    pass  # Don't fail if analytics is down
            
            return render_template("property_detail.html", p=prop)
        else:
            flash("Property not found", "error")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/properties/<int:property_id>/edit", methods=["GET", "POST"])
def edit_property(property_id: int):
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Unauthorized", "error")
        return redirect(url_for("index"))
    
    if request.method == "POST":
        data = {
            "title": request.form.get("title"),
            "description": request.form.get("description"),
            "city": request.form.get("city"),
            "address": request.form.get("address"),
            "price_eur": float(request.form.get("price_eur", 0)),
            "property_type": request.form.get("property_type"),
            "rooms": int(request.form.get("rooms", 0)) if request.form.get("rooms") else None,
            "area_m2": float(request.form.get("area_m2", 0)) if request.form.get("area_m2") else None,
            "is_for_sale": request.form.get("is_for_sale") == "on",
            "is_for_rent": request.form.get("is_for_rent") == "on"
        }
        
        try:
            response = requests.put(
                f"{PROPERTY_SERVICE_URL}/properties/{property_id}",
                json=data,
                headers=get_auth_headers(),
                timeout=5
            )
            
            if response.status_code == 200:
                flash("Property updated!", "success")
                return redirect(url_for("property_detail", property_id=property_id))
            else:
                flash(response.json().get("error", "Failed to update property"), "error")
        except Exception as e:
            flash(f"Service error: {str(e)}", "error")
    
    # Get property data
    try:
        response = requests.get(
            f"{PROPERTY_SERVICE_URL}/properties/{property_id}",
            timeout=5
        )
        if response.status_code == 200:
            prop = response.json()
            return render_template("property_edit.html", p=prop)
    except:
        pass
    
    flash("Property not found", "error")
    return redirect(url_for("index"))


@app.route("/properties/<int:property_id>/delete", methods=["POST"])
def property_delete(property_id: int):
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Unauthorized", "error")
        return redirect(url_for("index"))
    
    try:
        response = requests.delete(
            f"{PROPERTY_SERVICE_URL}/properties/{property_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            flash("Property deleted!", "success")
        else:
            flash(response.json().get("error", "Failed to delete property"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Proxy file serving to property service"""
    try:
        response = requests.get(
            f"{PROPERTY_SERVICE_URL}/uploads/{filename}",
            timeout=5,
            stream=True
        )
        
        if response.status_code == 200:
            from io import BytesIO
            return send_file(
                BytesIO(response.content),
                mimetype=response.headers.get('Content-Type', 'application/octet-stream')
            )
    except:
        pass
    
    from flask import abort
    abort(404)


# --- Search integration ---
@app.route("/search")
def search():
    q = request.args.get("q", "")
    city = request.args.get("city", "")
    property_type = request.args.get("property_type", "")

    # Track search event
    user = get_current_user()
    if user.is_authenticated and (q or city or property_type):
        try:
            search_query = f"q={q}, city={city}, type={property_type}".strip(", ")
            requests.post(
                f"{ANALYTICS_SERVICE_URL}/events",
                json={
                    "event_type": "search",
                    "user_id": user.id,
                    "metadata": search_query
                },
                timeout=2
            )
        except:
            pass

    try:
        resp = requests.get(
            f"{SEARCH_SERVICE_URL}/search",
            params={"q": q, "city": city, "property_type": property_type},
            timeout=5,
        )
        if resp.status_code == 200:
            properties = resp.json()
        else:
            properties = []
    except Exception as e:
        flash(f"Search service error: {str(e)}", "error")
        properties = []

    return render_template("properties.html", properties=properties)


@app.route("/search/index", methods=["POST"])
def rebuild_index():
    try:
        resp = requests.post(f"{SEARCH_SERVICE_URL}/index", timeout=10)
        if resp.status_code in (200, 201):
            flash("Search index rebuilt", "success")
        else:
            flash("Failed to rebuild search index", "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    return redirect(url_for("index"))


# --- Notification integration ---
@app.route("/notifications", methods=["POST"])
def create_notification():
    user = get_current_user()
    data = {
        "recipient": request.form.get("recipient"),
        "channel": request.form.get("channel", "email"),
        "message": request.form.get("message"),
    }
    headers = get_auth_headers() if user.is_authenticated else {}
    try:
        resp = requests.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            json=data,
            headers=headers,
            timeout=5,
        )
        if resp.status_code == 201:
            flash("Notification sent!", "success")
        else:
            flash(resp.json().get("error", "Failed to send notification"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    return redirect(url_for("index"))


@app.route("/notifications", methods=["GET"])
def list_notifications():
    user = get_current_user()
    if not user.is_authenticated:
        return redirect(url_for("login"))
    
    token = session.get("token")
    print(f"[DEBUG] Session token: {token[:20] if token else 'NONE'}...")
    
    headers = get_auth_headers()
    print(f"[DEBUG] Headers: {headers}")
    
    notifications = []
    error_msg = None
    
    try:
        print(f"[DEBUG] Calling {NOTIFICATION_SERVICE_URL}/notifications")
        resp = requests.get(f"{NOTIFICATION_SERVICE_URL}/notifications", headers=headers, timeout=5)
        print(f"[DEBUG] Notification response status: {resp.status_code}")
        print(f"[DEBUG] User: {user.email}, Role: {user.role}")
        
        if resp.status_code == 200:
            notifications = resp.json()
            print(f"[DEBUG] Got {len(notifications)} notifications")
        else:
            error_msg = f"Status {resp.status_code}: {resp.text}"
            print(f"[DEBUG] Error response: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Exception getting notifications: {error_msg}")
        flash(f"Ошибка загрузки уведомлений: {error_msg}", "error")
    
    # Return JSON if ?debug=1
    if request.args.get('debug'):
        return jsonify({
            "user": {"email": user.email, "role": user.role},
            "token_in_session": bool(token),
            "headers_sent": headers,
            "notifications_count": len(notifications),
            "notifications": notifications[:3] if notifications else [],
            "error": error_msg
        })
    
    print(f"[DEBUG] Rendering template with {len(notifications)} notifications")
    return render_template("notifications.html", notifications=notifications)


# Inquiry routes
@app.route("/properties/<int:property_id>/inquiry", methods=["POST"])
def create_inquiry(property_id: int):
    user = get_current_user()
    
    data = {
        "property_id": property_id,
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "phone": request.form.get("phone"),
        "message": request.form.get("message")
    }
    
    # If user is authenticated, use their email
    if user.is_authenticated and not data.get("email"):
        data["email"] = user.email
    
    try:
        # Send token if user is authenticated
        headers = get_auth_headers() if user.is_authenticated else {}
        response = requests.post(
            f"{INQUIRY_SERVICE_URL}/inquiries",
            json=data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 201:
            flash("Inquiry submitted!", "success")
            
            # Track inquiry creation event
            if user.is_authenticated:
                try:
                    requests.post(
                        f"{ANALYTICS_SERVICE_URL}/events",
                        json={
                            "event_type": "inquiry_create",
                            "resource_id": property_id,
                            "user_id": user.id,
                            "metadata": f"Создана заявка на объект #{property_id}"
                        },
                        timeout=2
                    )
                except:
                    pass
        else:
            flash(response.json().get("error", "Failed to submit inquiry"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(url_for("property_detail", property_id=property_id))


@app.route("/my_inquiries")
def my_inquiries():
    user = get_current_user()
    if not user.is_authenticated:
        return redirect(url_for("index"))
    
    # Только пользователи и админы могут видеть свои заявки
    if user.role not in ['user', 'admin']:
        return redirect(url_for("index"))
    
    try:
        # inquiry-service уже фильтрует заявки:
        # - агенты видят все
        # - пользователи видят только свои (по email через Client)
        response = requests.get(
            f"{INQUIRY_SERVICE_URL}/inquiries",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            inquiries = response.json()
        else:
            inquiries = []
    except Exception as e:
        flash(f"Ошибка загрузки заявок: {str(e)}", "error")
        inquiries = []
    
    return render_template("my_inquiries.html", inquiries=inquiries)


@app.route("/inquiries/<int:inquiry_id>/delete", methods=["POST"])
def delete_inquiry(inquiry_id: int):
    user = get_current_user()
    if not user.is_authenticated:
        return redirect(url_for("index"))
    
    try:
        response = requests.delete(
            f"{INQUIRY_SERVICE_URL}/inquiries/{inquiry_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            flash("Заявка успешно удалена", "success")
        else:
            try:
                error_msg = response.json().get("error", "Не удалось удалить заявку")
            except:
                error_msg = f"Ошибка {response.status_code}: {response.text}"
            flash(error_msg, "error")
    except requests.exceptions.RequestException as e:
        flash(f"Ошибка при удалении: {str(e)}", "error")
    except Exception as e:
        flash(f"Непредвиденная ошибка: {str(e)}", "error")
    
    return redirect(url_for("my_inquiries"))


@app.route("/all_inquiries")
def all_inquiries():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        return redirect(url_for("index"))
    
    try:
        response = requests.get(
            f"{INQUIRY_SERVICE_URL}/inquiries",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            inquiries = response.json()
        else:
            inquiries = []
    except:
        inquiries = []
    
    return render_template("all_inquiries.html", inquiries=inquiries)


@app.route("/inquiry/<int:inquiry_id>/status", methods=["POST"])
def change_inquiry_status(inquiry_id: int):
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        return redirect(url_for("index"))
    
    new_status = request.form.get("status")
    
    try:
        response = requests.put(
            f"{INQUIRY_SERVICE_URL}/inquiries/{inquiry_id}/status",
            json={"status": new_status},
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            flash("Inquiry status updated!", "success")
        else:
            flash(response.json().get("error", "Failed to update status"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(url_for("all_inquiries"))


# Appointment routes
@app.route("/appointments", methods=["GET", "POST"])
def appointments():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        data = {
            "property_id": int(request.form.get("property_id", 0)),
            "client_name": request.form.get("client_name"),
            "client_email": request.form.get("client_email"),
            "client_phone": request.form.get("client_phone"),
            "scheduled_at": request.form.get("scheduled_at"),
            "note": request.form.get("note")
        }
        
        try:
            response = requests.post(
                f"{INQUIRY_SERVICE_URL}/appointments",
                json=data,
                headers=get_auth_headers(),
                timeout=5
            )
            
            if response.status_code == 201:
                flash("Appointment scheduled!", "success")
            else:
                flash(response.json().get("error", "Failed to schedule appointment"), "error")
        except Exception as e:
            flash(f"Service error: {str(e)}", "error")
    
    # Get appointments and properties
    appointments_list = []
    properties = []
    
    try:
        response = requests.get(
            f"{INQUIRY_SERVICE_URL}/appointments",
            headers=get_auth_headers(),
            timeout=5
        )
        if response.status_code == 200:
            appointments_list = response.json()
    except:
        pass
    
    try:
        response = requests.get(f"{PROPERTY_SERVICE_URL}/properties", timeout=5)
        if response.status_code == 200:
            properties = response.json()
    except:
        pass
    
    return render_template("appointments.html", appointments=appointments_list, properties=properties)


# Project routes
@app.route("/projects", methods=["POST"])
def create_project():
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    name = request.form.get("name", "").strip()
    
    try:
        response = requests.post(
            f"{PROJECT_SERVICE_URL}/projects",
            json={"name": name},
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 201:
            flash("Project created!", "success")
        else:
            flash(response.json().get("error", "Failed to create project"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(url_for("index"))


@app.route("/projects/<int:project_id>")
def view_project(project_id: int):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    try:
        response = requests.get(
            f"{PROJECT_SERVICE_URL}/projects/{project_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            project = response.json()
            tasks = project.get("tasks", [])
            return render_template("project_detail.html", project=project, tasks=tasks)
        else:
            flash("Project not found", "error")
            return redirect(url_for("index"))
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
def create_task(project_id: int):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    data = {
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "status": request.form.get("status", "todo"),
        "priority": int(request.form.get("priority", 2)),
        "due_date": request.form.get("due_date")
    }
    
    try:
        response = requests.post(
            f"{PROJECT_SERVICE_URL}/projects/{project_id}/tasks",
            json=data,
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 201:
            flash("Task created!", "success")
        else:
            flash(response.json().get("error", "Failed to create task"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(url_for("view_project", project_id=project_id))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id: int):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    try:
        response = requests.post(
            f"{PROJECT_SERVICE_URL}/tasks/{task_id}/toggle",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code != 200:
            flash(response.json().get("error", "Failed to toggle task"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id: int):
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    try:
        response = requests.delete(
            f"{PROJECT_SERVICE_URL}/tasks/{task_id}",
            headers=get_auth_headers(),
            timeout=5
        )
        
        if response.status_code == 200:
            flash("Task deleted!", "success")
        else:
            flash(response.json().get("error", "Failed to delete task"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("index"))


# --- Analytics Service routes ---
@app.route("/analytics")
def analytics():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Доступ запрещён", "error")
        return redirect(url_for("index"))
    
    stats = {}
    events = []
    
    try:
        # Get statistics
        resp = requests.get(f"{ANALYTICS_SERVICE_URL}/stats", headers=get_auth_headers(), timeout=5)
        if resp.status_code == 200:
            stats = resp.json()
    except:
        flash("Analytics service unavailable", "error")
    
    try:
        # Get recent events
        resp = requests.get(f"{ANALYTICS_SERVICE_URL}/events?limit=20", headers=get_auth_headers(), timeout=5)
        if resp.status_code == 200:
            events = resp.json()
    except:
        pass
    
    return render_template("analytics.html", stats=stats, events=events)


@app.route("/analytics/track", methods=["POST"])
def track_event():
    user = get_current_user()
    
    # Получаем данные из JSON
    data = request.get_json() or {}
    
    payload = {
        "event_type": data.get("event_type", "page_view"),
        "user_id": user.id if user.is_authenticated else None,
        "metadata": data.get("page", "")
    }
    
    try:
        resp = requests.post(
            f"{ANALYTICS_SERVICE_URL}/events", 
            json=payload, 
            headers=get_auth_headers(), 
            timeout=5
        )
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Reporting Service routes ---
@app.route("/reports")
def reports():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Доступ запрещён", "error")
        return redirect(url_for("index"))
    
    return render_template("reports.html")


@app.route("/reports/properties", methods=["GET"])
def report_properties():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        resp = requests.get(f"{REPORTING_SERVICE_URL}/reports/properties", headers=get_auth_headers(), timeout=10)
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Failed to generate report"}), 500


@app.route("/reports/inquiries", methods=["GET"])
def report_inquiries():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        return jsonify({"error": "Unauthorized"}), 403
    
    try:
        resp = requests.get(f"{REPORTING_SERVICE_URL}/reports/inquiries", headers=get_auth_headers(), timeout=10)
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Failed to generate report"}), 500


# --- Payment Service routes ---
@app.route("/payments/new", methods=["POST"])
def create_payment():
    user = get_current_user()
    if not user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = {
        "amount": float(request.form.get("amount", 0)),
        "currency": request.form.get("currency", "EUR"),
        "property_id": int(request.form.get("property_id", 0)) if request.form.get("property_id") else None
    }
    
    try:
        resp = requests.post(f"{PAYMENT_SERVICE_URL}/transactions", json=data, headers=get_auth_headers(), timeout=5)
        if resp.status_code == 201:
            flash("Платёж успешно создан!", "success")
            return redirect(url_for("my_payments"))
        else:
            flash(resp.json().get("error", "Ошибка платежа"), "error")
    except Exception as e:
        flash(f"Service error: {str(e)}", "error")
    
    return redirect(request.referrer or url_for("index"))


@app.route("/my_payments")
@app.route("/payments")
def my_payments():
    user = get_current_user()
    if not user.is_authenticated:
        return redirect(url_for("login"))
    
    transactions = []
    try:
        resp = requests.get(f"{PAYMENT_SERVICE_URL}/transactions", headers=get_auth_headers(), timeout=5)
        if resp.status_code == 200:
            transactions = resp.json()
    except:
        flash("Payment service unavailable", "error")
    
    return render_template("payments.html", transactions=transactions)


# --- Media Service routes ---
@app.route("/media/upload", methods=["POST"])
def upload_media():
    user = get_current_user()
    if not user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        files = {'file': (file.filename, file.stream, file.content_type)}
        resp = requests.post(f"{MEDIA_SERVICE_URL}/upload", files=files, headers=get_auth_headers(), timeout=30)
        if resp.status_code == 201:
            return jsonify(resp.json()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Upload failed"}), 500


# --- Logging Service routes ---
@app.route("/logs")
def view_logs():
    user = get_current_user()
    if not user.is_authenticated or user.role != "agent":
        flash("Доступ запрещён", "error")
        return redirect(url_for("index"))
    
    logs = []
    try:
        resp = requests.get(f"{LOGGING_SERVICE_URL}/logs?limit=100", headers=get_auth_headers(), timeout=5)
        if resp.status_code == 200:
            logs = resp.json()
    except:
        flash("Logging service unavailable", "error")
    
    return render_template("logs.html", logs=logs)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

