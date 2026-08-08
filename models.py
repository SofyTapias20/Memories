from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()

CATEGORIES = ["Cuidado Personal (Self-care)", "Ocio Activo", "Ocio Pasivo", "Académico / Enfoque", "Social", "Gastronómico", "Cultura", "Creatividad", "Naturaleza", "Gaming", "Música", "Películas / Series", "Mindfulness", "Fitness", "Tecnología", "Finanzas Personales", "Organización", "Viajes", "Familia", "Mascotas"]
MOODS = ["Productivo", "Agotado (Socialmente)", "Aventurero / Enérgico", "Agobiado / Estresado", "Aburrido", "Inspirado", "Feliz", "Triste", "Ansioso", "Motivado", "Cansado", "Curioso", "Nostálgico", "Relajado", "Solitario", "Creativo", "Sin Energía", "Distraído"]

SEED_ACTIVITIES = [
    ("Rutina skincare nocturna", "Cuidado Personal (Self-care)", "Relajado", 25, 0, "Relajante, Cuidado, Noche, Bienestar", "Limpieza facial, hidratación y una pausa tranquila antes de dormir."),
    ("Caminata por el barrio", "Ocio Activo", "Aventurero / Enérgico", 45, 0, "Caminar, Fotografía, Activo, Explorar", "Salir a caminar y capturar detalles interesantes del entorno."),
    ("Lectura tranquila de un libro", "Ocio Pasivo", "Cansado", 30, 0, "Lectura, Descanso, Calma, Casa", "Leer sin presión un capítulo corto o varias páginas de un libro."),
    ("Sesión de Pomodoro para realizar una tarea", "Académico / Enfoque", "Productivo", 50, 0, "Estudio, Enfoque, Pomodoro, Productivo", "Dos bloques de 25 minutos para avanzar en una tarea concreta."),
    ("Café corto con un amigo", "Social", "Feliz", 60, 8000, "Social, Café, Conversación, Amigos", "Un encuentro sencillo para conversar y despejar la mente."),
    ("Cena casera temática", "Gastronómico", "Inspirado", 90, 18000, "Cocina, Comida, Creativo, Hogar", "Preparar una receta especial con música y una mesa bonita."),
    ("Dibujo libre con referencia", "Creatividad", "Creativo", 45, 0, "Dibujo, Arte, Creativo, Expresión", "Elegir una imagen de referencia y dibujar sin buscar perfección."),
    ("Picnic simple en un parque", "Naturaleza", "Relajado", 75, 12000, "Parque, Naturaleza, Aire Libre, Picnic", "Llevar algo ligero para comer y descansar al aire libre."),
    ("Partida cooperativa online", "Gaming", "Aburrido", 60, 0, "Gaming, Online, Cooperativo, Diversión", "Jugar una partida con amigos o comunidad sin modo competitivo intenso."),
    ("Crear playlist de música", "Música", "Motivado", 20, 0, "Música, Playlist, Ordenar, Energía", "Armar una lista de canciones y ordenar una zona pequeña."),
    ("Episodio piloto de una serie", "Películas / Series", "Sin Energía", 45, 0, "Series, Descanso, Sofá, Entretenimiento", "Ver un episodio corto y decidir si vale la pena continuarla."),
    ("Meditación guiada de respiración", "Mindfulness", "Ansioso", 12, 0, "Meditación, Respiración, Ansiedad, Calma", "Hacer una práctica breve enfocada en respiración lenta."),
    ("Rutina HIIT suave", "Fitness", "Motivado", 25, 0, "Ejercicio, Fitness, Energía, Casa", "Ejercicios cortos de bajo impacto para activar el cuerpo."),
    ("Aprender un atajo digital útil", "Tecnología", "Curioso", 20, 0, "Tecnología, Productividad, Aprender, Herramientas", "Ver un tutorial corto y aplicar un atajo en una app que uses."),
    ("Revisión de presupuesto semanal", "Finanzas Personales", "Productivo", 35, 0, "Finanzas, Presupuesto, Organización, Dinero", "Revisar gastos recientes y definir un límite para la semana."),
    ("Reset de escritorio en 15 minutos", "Organización", "Distraído", 15, 0, "Orden, Escritorio, Enfoque, Limpieza", "Quitar basura, agrupar pendientes y dejar solo lo necesario."),
    ("Plan express de escapada local", "Viajes", "Nostálgico", 40, 0, "Viajes, Planear, Mapa, Escapada", "Buscar una ruta cercana, costos y tres lugares para visitar."),
    ("Llamada familiar con tema bonito", "Familia", "Solitario", 30, 0, "Familia, Llamada, Conexión, Conversar", "Llamar a alguien de la familia y preguntarle por un recuerdo feliz."),
    ("Paseo consciente con mascota", "Mascotas", "Agobiado / Estresado", 30, 0, "Mascotas, Paseo, Calma, Exterior", "Salir sin prisa, dejar que la mascota explore y respirar profundo."),
    ("Baño relajante con música suave", "Cuidado Personal (Self-care)", "Triste", 35, 4000, "Relajante, Autocuidado, Música, Descanso", "Una rutina de cuidado personal para recuperar energía emocional."),
    ("Mini ruta en bicicleta", "Ocio Activo", "Aventurero / Enérgico", 60, 0, "Bicicleta, Activo, Exterior, Explorar", "Elegir una ruta segura y pedalear a ritmo cómodo."),
    ("Diario de ideas en papel", "Creatividad", "Inspirado", 20, 0, "Ideas, Escribir, Creativo, Journaling", "Anotar diez ideas sin juzgarlas y elegir una para desarrollar."),
    ("Ordenar archivos digitales", "Tecnología", "Distraído", 30, 0, "Tecnología, Organización, Archivos, Productividad", "Limpiar descargas, crear carpetas y borrar duplicados evidentes."),
    ("Noche de película clásica", "Películas / Series", "Nostálgico", 120, 6000, "Películas, Clásicos, Nostalgia, Descanso", "Escoger una película querida o histórica y verla con calma."),
    ("Estiramientos para soltar tensión", "Fitness", "Agobiado / Estresado", 18, 0, "Estiramientos, Cuerpo, Tensión, Bienestar", "Movimientos suaves de cuello, espalda y piernas."),
    ("Noche offline radical", "Tecnología", "Agobiado / Estresado", 180, 0, "Digital Detox, Descanso, Offline, Calma", "Apagar todas las pantallas y sobrevivir una noche completa usando solo actividades físicas o analógicas."),
    ("Llamada con los Tres Mosqueteros", "Social", "Feliz", 40, 0, "Tecnología, Comunicación, Social, Alegría", "Aquí lograrás hablar con los mejores, no lo olvides J+S^2.")
]

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), unique=True, nullable=False, index=True)
    category = db.Column(db.String(120), nullable=False)
    mood = db.Column(db.String(120), nullable=False)
    minutes = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    tags = db.Column(db.String(255), default="", nullable=False)
    description = db.Column(db.Text)
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def tag_list(self):
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]


class Favorite(db.Model):
    __tablename__ = "favorites"
    __table_args__ = (db.UniqueConstraint("user_id", "activity_id", name="unique_favorite"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref="favorites")
    activity = db.relationship("Activity", backref="favorites")


class RecommendationHistory(db.Model):
    __tablename__ = "recommendation_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activities.id"), nullable=False)
    available_minutes = db.Column(db.Integer, nullable=False)
    mood = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref="recommendations")
    activity = db.relationship("Activity", backref="recommendations")


class Suggestion(db.Model):
    __tablename__ = "suggestions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    mood = db.Column(db.String(120), nullable=False)
    minutes = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    tags = db.Column(db.String(255), default="", nullable=False)
    message = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255))
    status = db.Column(db.String(30), default="Pendiente", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user = db.relationship("User", backref="suggestions")