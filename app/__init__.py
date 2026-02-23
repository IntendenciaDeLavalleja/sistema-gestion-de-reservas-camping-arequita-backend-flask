from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.extensions import db, migrate, login_manager, mail, ma, limiter, csrf
from app.services.minio_service import minio_service
from app.services.cache_service import cache_service
from app.metrics import init_metrics

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Habilitar CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])}},
        supports_credentials=True
    )

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    ma.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Inicializar servicios
    minio_service.init_app(app)
    cache_service.init_app(app)

    # Inicializar monitoreo
    init_metrics(app)

    # Registrar blueprints
    from app.api import api_bp
    csrf.exempt(api_bp) # Eximir API de protección CSRF (usa tokens Bearer)
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Registrar comandos CLI
    from app.commands import create_admin, init_db, archive_expired_pre_reservations_command
    from app.seed_command import seed_data
    app.cli.add_command(create_admin)
    app.cli.add_command(init_db)
    app.cli.add_command(archive_expired_pre_reservations_command)
    app.cli.add_command(seed_data)
    
    # Cargar modelos para migraciones
    from app import models

    return app

from app.models import AdminUser

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))
