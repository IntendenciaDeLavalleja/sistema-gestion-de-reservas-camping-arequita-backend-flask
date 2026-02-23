import json
import redis
from ..redis_utils import build_redis_url_from_env


class CacheService:
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        redis_url = app.config.get('REDIS_URL') or build_redis_url_from_env()
        try:
            self.client = redis.from_url(redis_url)
            # Test connection
            self.client.ping()
        except Exception as e:
            app.logger.warning(f"No se pudo conectar a Redis para caché: {e}")
            self.client = None

    def get(self, key):
        """Obtiene un valor del caché."""
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Error al obtener de caché ({key}): {e}")
        return None

    def set(self, key, value, timeout=300):
        """Guarda un valor en el caché."""
        if not self.client:
            return False
        try:
            data = json.dumps(value)
            return self.client.setex(key, timeout, data)
        except Exception as e:
            print(f"Error al guardar en caché ({key}): {e}")
        return False

    def delete(self, key):
        """Elimina una llave del caché."""
        if not self.client:
            return False
        try:
            return self.client.delete(key)
        except Exception as e:
            print(f"Error al eliminar de caché ({key}): {e}")
        return False

    def clear_prefix(self, prefix):
        """Elimina todas las llaves que empiecen con un prefijo."""
        if not self.client:
            return False
        try:
            keys = self.client.keys(f"{prefix}*")
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            print(f"Error al limpiar prefijo de caché ({prefix}): {e}")
        return False


# Instancia global para ser inicializada en create_app
cache_service = CacheService()
