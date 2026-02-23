from flask import render_template
from flask_login import login_required
from sqlalchemy.orm import joinedload
from app.models.camping import CampingService, ServiceTestimonial, PreReservation, Suggestion
from app.services.reservation_service import archive_expired_pre_reservations
from . import admin_bp

# Importar todos los componentes de rutas
from .routes_components import auth
from .routes_components import localities
from .routes_components import procedures
from .routes_components import slots
from .routes_components import reservations
from .routes_components import audit
from .routes_components import amenities
from .routes_components import services
from .routes_components import hero_images
from .routes_components import reviews
from .routes_components import pre_reservations
from .routes_components import suggestions
from .routes_components import media_cleanup

@admin_bp.route('/')
@login_required
def dashboard():
    archive_expired_pre_reservations()

    total_services = CampingService.query.count()
    featured_services = CampingService.query.filter_by(is_featured=True).count()
    total_testimonials = ServiceTestimonial.query.count()
    published_testimonials = ServiceTestimonial.query.filter_by(is_published=True).count()
    pending_pre_reservations = PreReservation.query.filter_by(status='pendiente')
    confirmed_pre_reservations = PreReservation.query.filter_by(status='confirmado')
    active_stays = PreReservation.query.filter_by(status='activo')
    new_suggestions = Suggestion.query.filter_by(status='nuevo')

    recent_pre_reservations = PreReservation.query.options(
        joinedload(PreReservation.service)
    ).order_by(PreReservation.created_at.desc()).limit(10).all()

    recent_suggestions = Suggestion.query.order_by(Suggestion.created_at.desc()).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total_services=total_services,
        featured_services=featured_services,
        total_testimonials=total_testimonials,
        published_testimonials=published_testimonials,
        pending_pre_reservations=pending_pre_reservations.count(),
        confirmed_pre_reservations=confirmed_pre_reservations.count(),
        active_stays=active_stays.count(),
        new_suggestions=new_suggestions.count(),
        recent_pre_reservations=recent_pre_reservations,
        recent_suggestions=recent_suggestions,
    )
