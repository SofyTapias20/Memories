import os
from decimal import Decimal, InvalidOperation
from functools import wraps
from uuid import uuid4
from flask import Blueprint, current_app, flash, g, redirect, render_template, request, session, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from models import Activity, CATEGORIES, Favorite, MOODS, RecommendationHistory, Suggestion, User, db
auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)
admin_bp = Blueprint("admin", __name__)
ALLOWED_IMAGE_EXTENSIONS = {"gif", "jpg", "jpeg", "png", "webp"}

def text(value):
    return (value or "").strip()
def email(value):
    return text(value).lower()
def number(value, minimum=1):
    try:
        value = int(value)
        return value if value >= minimum else None
    except (TypeError, ValueError):
        return None
def money(value):
    try:
        value = Decimal(str(value or "0")).quantize(Decimal("0.01"))
        return value if value >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_image(field_name="image"):
    uploaded_file = request.files.get(field_name)
    if not uploaded_file or not uploaded_file.filename:
        return None
    if not allowed_image(uploaded_file.filename):
        raise ValueError("Solo se permiten imagenes JPG, JPEG, PNG, GIF o WEBP.")

    original_name = secure_filename(uploaded_file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    filename = f"{uuid4().hex}.{extension}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    uploaded_file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename


def delete_uploaded_image(filename):
    if not filename:
        return
    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    file_path = os.path.abspath(os.path.join(upload_folder, filename))
    if file_path.startswith(upload_folder) and os.path.exists(file_path):
        os.remove(file_path)


def activity_form_data():
    minutes = number(request.form.get("minutes"), 5)
    cost = money(request.form.get("cost"))
    data = {key: text(request.form.get(key)) for key in ["name", "category", "mood", "tags", "description"]}
    valid = (
        data["name"]
        and data["tags"]
        and data["category"] in CATEGORIES
        and data["mood"] in MOODS
        and minutes
        and cost is not None
    )
    return data, minutes, cost, valid


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.user:
            flash("Debes iniciar sesion.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(*args, **kwargs)
    return wrapper
def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.user:
            return redirect(url_for("auth.login", next=request.path))
        if not g.user.is_admin:
            flash("No tienes permisos de administrador.", "danger")
            return redirect(url_for("main.home"))
        return view(*args, **kwargs)
    return wrapper
def reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
def reset_token(user_email):
    return reset_serializer().dumps(user_email, salt=current_app.config["SECURITY_PASSWORD_SALT"])
def token_email(token):
    try:
        return reset_serializer().loads(
            token,
            salt=current_app.config["SECURITY_PASSWORD_SALT"],
            max_age=current_app.config["RESET_TOKEN_MAX_AGE"],
        )
    except (BadSignature, SignatureExpired):
        return None
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = text(request.form.get("name"))
        user_email = email(request.form.get("email"))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if not name or not user_email or not password:
            flash("Todos los campos son obligatorios.", "danger")
        elif password != confirm:
            flash("Las contraseñas no coinciden.", "danger")
        elif len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "danger")
        elif User.query.filter_by(email=user_email).first():
            flash("Ese email ya esta registrado.", "warning")
        else:
            user = User(name=name, email=user_email, is_admin=User.query.count() == 0)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Cuenta creada. Ahora inicia sesion.", "success")
            return redirect(url_for("auth.login"))
    return render_template("register.html", title="Registro")
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=email(request.form.get("email"))).first()
        password = request.form.get("password", "")
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            return redirect(request.args.get("next") or url_for("main.home"))
        flash("Credenciales incorrectas.", "danger")
    return render_template("login.html", title="Login")
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Sesion cerrada.", "info")
    return redirect(url_for("auth.login"))
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    link = None
    if request.method == "POST":
        user = User.query.filter_by(email=email(request.form.get("email"))).first()
        if user:
            link = url_for("auth.reset_password", token=reset_token(user.email), _external=True)
            current_app.logger.info("Reset password: %s", link)
        flash("Si el email existe, se genero un enlace temporal.", "success")
    return render_template("forgot_password.html", title="Recuperar contraseña", reset_link=link)
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(email=token_email(token)).first()
    if not user:
        flash("El enlace es invalido o expiro.", "danger")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if password and password == confirm and len(password) >= 8:
            user.set_password(password)
            db.session.commit()
            flash("Contrasena actualizada.", "success")
            return redirect(url_for("auth.login"))
        flash("Revisa que las contraseñas coincidan y tengan minimo 8 caracteres.", "danger")
    return render_template("reset_password.html", title="Nueva contraseña")
@auth_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    name = text(request.form.get("name"))
    user_email = email(request.form.get("email"))
    repeated = User.query.filter(User.email == user_email, User.id != g.user.id).first()
    if not name or not user_email:
        flash("Nombre y email son obligatorios.", "danger")
    elif repeated:
        flash("Ese email ya pertenece a otro usuario.", "warning")
    else:
        g.user.name = name
        g.user.email = user_email
        db.session.commit()
        flash("Perfil actualizado.", "success")
    return redirect(url_for("main.mine"))
@main_bp.route("/")
@login_required
def home():
    return render_template(
        "home.html",
        title="Inicio",
        total_activities=Activity.query.count(),
        total_favorites=Favorite.query.filter_by(user_id=g.user.id).count(),
        recent_activities=Activity.query.order_by(Activity.created_at.desc()).limit(6).all(),
    )
@main_bp.route("/questionnaire", methods=["GET", "POST"])
@login_required
def questionnaire():
    if request.method == "POST":
        minutes = number(request.form.get("minutes"), 5)
        budget = money(request.form.get("budget"))
        mood = text(request.form.get("mood"))
        if not minutes or budget is None or mood not in MOODS:
            flash("Completa el cuestionario con datos validos.", "danger")
        else:
            results = Activity.query.filter(Activity.minutes <= minutes, Activity.cost <= budget, Activity.mood == mood).all()
            fallback = False
            if not results:
                results = Activity.query.filter(Activity.minutes <= minutes, Activity.cost <= budget).limit(8).all()
                fallback = True
            for activity in results[:8]:
                db.session.add(RecommendationHistory(user_id=g.user.id, activity_id=activity.id, available_minutes=minutes, mood=mood, budget=budget))
            db.session.commit()
            return render_template("results.html", title="Resultados", results=results, minutes=minutes, budget=budget, mood=mood, fallback_used=fallback)
    return render_template("questionnaire.html", title="Cuestionario", moods=MOODS)
@main_bp.route("/activities")
@login_required
def activities():
    query = Activity.query
    category = text(request.args.get("category"))
    mood = text(request.args.get("mood"))
    max_minutes = number(request.args.get("max_minutes"), 1) if request.args.get("max_minutes") else None
    max_cost = money(request.args.get("max_cost")) if request.args.get("max_cost") else None
    if category in CATEGORIES:
        query = query.filter_by(category=category)
    if mood in MOODS:
        query = query.filter_by(mood=mood)
    if max_minutes:
        query = query.filter(Activity.minutes <= max_minutes)
    if max_cost is not None:
        query = query.filter(Activity.cost <= max_cost)
    return render_template("activities.html", title="Actividades", activities=query.order_by(Activity.name).all(), categories=CATEGORIES, moods=MOODS, selected_category=category, selected_mood=mood)
@main_bp.route("/activities/<int:activity_id>")
@login_required
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    return render_template("activities.html", title=activity.name, activities=[activity], categories=CATEGORIES, moods=MOODS, selected_category="", selected_mood="", detail_activity=activity)


@main_bp.route("/activities/<int:activity_id>/image", methods=["POST"])
@login_required
def upload_activity_image(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    try:
        image_filename = save_uploaded_image()
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("main.activity_detail", activity_id=activity.id))

    if not image_filename:
        flash("Selecciona una imagen para subir.", "warning")
        return redirect(url_for("main.activity_detail", activity_id=activity.id))

    old_image = activity.image_filename
    activity.image_filename = image_filename
    db.session.commit()
    delete_uploaded_image(old_image)
    flash("Imagen de la actividad actualizada.", "success")
    return redirect(url_for("main.activity_detail", activity_id=activity.id))
@main_bp.route("/favorites/<int:activity_id>/toggle", methods=["POST"])
@login_required
def toggle_favorite(activity_id):
    Activity.query.get_or_404(activity_id)
    favorite = Favorite.query.filter_by(user_id=g.user.id, activity_id=activity_id).first()
    if favorite:
        db.session.delete(favorite)
    else:
        db.session.add(Favorite(user_id=g.user.id, activity_id=activity_id))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    return redirect(request.referrer or url_for("main.activities"))
@main_bp.route("/mine")
@login_required
def mine():
    favorites = Activity.query.join(Favorite).filter(Favorite.user_id == g.user.id).all()
    history = RecommendationHistory.query.filter_by(user_id=g.user.id).order_by(RecommendationHistory.created_at.desc()).limit(20).all()
    return render_template("mine.html", title="Mi espacio", favorites=favorites, history=history)
@main_bp.route("/search")
@login_required
def search():
    query = text(request.args.get("q"))
    results = Activity.query.filter(Activity.tags.ilike(f"%{query}%")).all() if query else []
    return render_template("search.html", title="Buscar", query=query, results=results)
@main_bp.route("/suggestions", methods=["GET", "POST"])
@login_required
def suggestions():
    if request.method == "POST":
        minutes = number(request.form.get("minutes"), 5)
        cost = money(request.form.get("cost"))
        data = {key: text(request.form.get(key)) for key in ["name", "category", "mood", "tags", "message"]}
        if not data["name"] or not data["tags"] or not data["message"] or data["category"] not in CATEGORIES or data["mood"] not in MOODS or not minutes or cost is None:
            flash("Completa la sugerencia con datos validos.", "danger")
        else:
            try:
                image_filename = save_uploaded_image()
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("main.suggestions"))
            db.session.add(Suggestion(user_id=g.user.id, minutes=minutes, cost=cost, image_filename=image_filename, **data))
            db.session.commit()
            flash("Sugerencia enviada al administrador.", "success")
            return redirect(url_for("main.suggestions"))
    query = Suggestion.query if g.user.is_admin else Suggestion.query.filter_by(user_id=g.user.id)
    return render_template("suggestions.html", title="Sugerencias", categories=CATEGORIES, moods=MOODS, suggestions=query.order_by(Suggestion.created_at.desc()).all())
@admin_bp.route("", methods=["GET", "POST"])
@admin_required
def admin_panel():
    if request.method == "POST":
        data, minutes, cost, valid = activity_form_data()
        if not valid:
            flash("Completa la actividad con datos validos.", "danger")
        elif Activity.query.filter_by(name=data["name"]).first():
            flash("Ya existe una actividad con ese nombre.", "warning")
        else:
            try:
                image_filename = save_uploaded_image()
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("admin.admin_panel"))
            db.session.add(Activity(minutes=minutes, cost=cost, image_filename=image_filename, **data))
            db.session.commit()
            flash("Actividad creada.", "success")
            return redirect(url_for("admin.admin_panel"))
    return render_template("admin.html", title="Admin", categories=CATEGORIES, moods=MOODS, activities=Activity.query.order_by(Activity.created_at.desc()).all(), suggestions=Suggestion.query.order_by(Suggestion.created_at.desc()).limit(12).all())


@admin_bp.route("/activities/<int:activity_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    if request.method == "POST":
        data, minutes, cost, valid = activity_form_data()
        repeated = Activity.query.filter(Activity.name == data["name"], Activity.id != activity.id).first()
        if not valid:
            flash("Completa la actividad con datos validos.", "danger")
        elif repeated:
            flash("Ya existe otra actividad con ese nombre.", "warning")
        else:
            try:
                image_filename = save_uploaded_image()
            except ValueError as error:
                flash(str(error), "danger")
                return redirect(url_for("admin.edit_activity", activity_id=activity.id))

            old_image = activity.image_filename
            activity.name = data["name"]
            activity.category = data["category"]
            activity.mood = data["mood"]
            activity.minutes = minutes
            activity.cost = cost
            activity.tags = data["tags"]
            activity.description = data["description"]
            if image_filename:
                activity.image_filename = image_filename
            db.session.commit()
            if image_filename:
                delete_uploaded_image(old_image)
            flash("Actividad actualizada.", "success")
            return redirect(url_for("admin.admin_panel"))
    return render_template("admin_edit.html", title="Editar actividad", categories=CATEGORIES, moods=MOODS, activity=activity)
@admin_bp.route("/activities/<int:activity_id>/delete", methods=["POST"])
@admin_required
def delete_activity(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    image_filename = activity.image_filename
    Favorite.query.filter_by(activity_id=activity.id).delete()
    RecommendationHistory.query.filter_by(activity_id=activity.id).delete()
    db.session.delete(activity)
    db.session.commit()
    delete_uploaded_image(image_filename)
    return redirect(url_for("admin.admin_panel"))
@admin_bp.route("/suggestions/<int:suggestion_id>/status", methods=["POST"])
@admin_required
def update_suggestion_status(suggestion_id):
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    if request.form.get("status") in {"Pendiente", "Revisada", "Aprobada", "Descartada"}:
        suggestion.status = request.form["status"]
        db.session.commit()
    return redirect(request.referrer or url_for("admin.admin_panel"))
