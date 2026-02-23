from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, login_manager, mail, ma, limiter, csrf
from .services.minio_service import minio_service
from .services.cache_service import cache_service
from .metrics import init_metrics
from .redis_utils import is_redis_available


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configurar storage de Flask-Limiter.
    # Si Redis no está disponible al boot, se usa memoria.
    redis_url = app.config.get('REDIS_URL')
    redis_available, redis_error = is_redis_available(redis_url)
    if redis_available:
        app.config['RATELIMIT_STORAGE_URI'] = redis_url
        app.logger.info("Flask-Limiter usando Redis como backend.")
    else:
        app.config['RATELIMIT_STORAGE_URI'] = 'memory://'
        if redis_error:
            app.logger.warning(
                "Redis no disponible para rate limiting, "
                f"fallback a memory:// ({redis_error})"
            )
    
    # Habilitar CORS
    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config.get('CORS_ALLOWED_ORIGINS', [])}
        },
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
    try:
        minio_service.init_app(app)
    except Exception as exc:
        app.logger.warning(
            "MinIO no disponible al iniciar, "
            f"se continúa sin cliente: {exc}"
        )

    cache_service.init_app(app)

    # Inicializar monitoreo
    init_metrics(app)

    # Registrar blueprints
    from .health import health_bp
    csrf.exempt(health_bp)
    app.register_blueprint(health_bp)

    from .api import api_bp
    csrf.exempt(api_bp)  # Eximir API de protección CSRF (usa tokens Bearer)
    app.register_blueprint(api_bp, url_prefix='/api')

    from .admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Registrar comandos CLI
    from .commands import (
        create_admin,
        init_db,
        archive_expired_pre_reservations_command,
    )
    from .seed_command import seed_data
    app.cli.add_command(create_admin)
    app.cli.add_command(init_db)
    app.cli.add_command(archive_expired_pre_reservations_command)
    app.cli.add_command(seed_data)
    
    # Cargar modelos para migraciones
    import importlib
    importlib.import_module('app.models')

    return app


@login_manager.user_loader
def load_user(user_id):
    from .models import AdminUser

    return AdminUser.query.get(int(user_id))
