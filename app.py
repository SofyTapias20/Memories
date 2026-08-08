import os
from urllib.parse import quote_plus

import pymysql
from flask import Flask, g, session
from sqlalchemy import inspect, text as sql_text
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

from models import Activity, Favorite, SEED_ACTIVITIES, User, db
from routes import admin_bp, auth_bp, main_bp


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_local_env(path):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


for env_path in (os.path.join(BASE_DIR, ".env"), os.path.join(BASE_DIR, "env")):
    load_dotenv(env_path)
    load_local_env(env_path)


def mysql_uri():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("mysql://"):
            database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
        return database_url

    user = quote_plus(os.getenv("MYSQL_USER", "root"))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "memories_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


def create_database(app):
    connection = pymysql.connect(
        host=app.config["MYSQL_HOST"],
        port=app.config["MYSQL_PORT"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        charset="utf8mb4",
        autocommit=True,
    )
    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{app.config['MYSQL_DATABASE']}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    connection.close()


def seed_data():
    if not User.query.filter_by(is_admin=True).first():
        admin = User(name="Administrador Memories", email="admin@memories.com", is_admin=True)
        admin.set_password("Admin123*")
        db.session.add(admin)

    existing_activities = {activity.name: activity for activity in Activity.query.all()}
    for name, category, mood, minutes, cost, tags, description in SEED_ACTIVITIES:
        activity = existing_activities.get(name)
        if activity:
            activity.cost = cost
        else:
            db.session.add(
                Activity(
                    name=name,
                    category=category,
                    mood=mood,
                    minutes=minutes,
                    cost=cost,
                    tags=tags,
                    description=description,
                )
            )
    db.session.commit()


def ensure_upload_folder(app):
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def ensure_optional_columns():
    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    optional_columns = {
        "activities": {"image_filename": "VARCHAR(255) NULL"},
        "suggestions": {"image_filename": "VARCHAR(255) NULL"},
    }

    for table_name, columns in optional_columns.items():
        if table_name not in tables:
            continue
        existing = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name, definition in columns.items():
            if column_name not in existing:
                db.session.execute(
                    sql_text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
                )
    db.session.commit()


def format_cop(value):
    amount = float(value or 0)
    formatted = f"{amount:,.0f}".replace(",", ".")
    return f"COP ${formatted}"


def create_app():
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "memories-dev-secret"),
        SECURITY_PASSWORD_SALT=os.getenv("SECURITY_PASSWORD_SALT", "memories-reset-salt"),
        MYSQL_HOST=os.getenv("MYSQL_HOST", "127.0.0.1"),
        MYSQL_PORT=int(os.getenv("MYSQL_PORT", "3306")),
        MYSQL_USER=os.getenv("MYSQL_USER", "root"),
        MYSQL_PASSWORD=os.getenv("MYSQL_PASSWORD", ""),
        MYSQL_DATABASE=os.getenv("MYSQL_DATABASE", "memories_db"),
        SQLALCHEMY_DATABASE_URI=mysql_uri(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        RESET_TOKEN_MAX_AGE=3600,
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    )

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.before_request
    def load_user():
        g.user = db.session.get(User, session["user_id"]) if session.get("user_id") else None

    @app.context_processor
    def template_helpers():
        def is_favorite(activity_id):
            return bool(
                g.user
                and Favorite.query.filter_by(user_id=g.user.id, activity_id=activity_id).first()
            )

        return {"current_user": g.get("user"), "is_favorite": is_favorite, "format_cop": format_cop}

    with app.app_context():
        ensure_upload_folder(app)
        # En local se crea la base de datos si todavía no existe.
        # En Railway la base ya existe y la conexión llega mediante DATABASE_URL.
        if not os.getenv("DATABASE_URL"):
            create_database(app)
        db.create_all()
        ensure_optional_columns()
        seed_data()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)