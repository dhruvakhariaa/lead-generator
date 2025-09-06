# app/services/__init__.py
# Keep this file empty or with minimal imports to prevent circular dependencies
# Services should be imported directly where needed via ServiceFactory

from app.services.service_factory import ServiceFactory

__all__ = ['ServiceFactory']