#routes/__init__.py
from .sync import sync_bp
from .export import export_bp
from .change_password import passwd_bp

__all__ = ['sync_bp','export_bp','passwd_bp']