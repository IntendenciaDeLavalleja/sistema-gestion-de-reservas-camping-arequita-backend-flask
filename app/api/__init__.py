from datetime import datetime, timedelta
import json
import random
import string
import uuid
from flask import Blueprint, jsonify, request
from werkzeug.datastructures import MultiDict
from wtforms import Form, StringField, IntegerField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange
from app.extensions import db
from app.services.cache_service import cache_service
from app.models.camping import CampingService, HeroImage, ServiceTestimonial, PreReservation, Suggestion
from app.services.email_service import send_camping_pre_reservation_email
from app.services.reservation_service import archive_expired_pre_reservations, confirm_pre_reservation

api_bp = Blueprint('api', __name__)

# Registrar rutas API de autenticación (2FA para panel/app externa)
from . import auth


class PreReservationForm(Form):
    service_id = IntegerField('service_id', validators=[DataRequired()])
    full_name = StringField('full_name', validators=[DataRequired(), Length(min=2, max=140)])
    email = StringField('email', validators=[DataRequired(), Email(), Length(max=140)])
    phone = StringField('phone', validators=[DataRequired(), Length(min=6, max=40)])
    guests = IntegerField('guests', validators=[DataRequired(), NumberRange(min=1, max=20)])
    check_in = DateField('check_in', validators=[DataRequired()], format='%Y-%m-%d')
    check_out = DateField('check_out', validators=[DataRequired()], format='%Y-%m-%d')
    notes = TextAreaField('notes', validators=[Length(max=2000)])
    lang = StringField('lang', validators=[Length(max=5)])


class SuggestionForm(Form):
    name = StringField('name', validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField('email', validators=[DataRequired(), Email(), Length(max=140)])
    category = StringField('category', validators=[DataRequired(), Length(min=2, max=50)])
    message = TextAreaField('message', validators=[DataRequired(), Length(min=10, max=3000)])
    lang = StringField('lang', validators=[Length(max=5)])


def _safe_lang(value: str | None) -> str:
    if value in ('es', 'en', 'pt'):
        return value
    return 'es'


def _generate_pre_reservation_code() -> str:
    letters = ''.join(random.choice(string.ascii_uppercase) for _ in range(3))
    numbers = ''.join(random.choice(string.digits) for _ in range(4))
    return f'ARQ-{letters}-{numbers}'


def _request_payload() -> dict:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload

    if request.form:
        return request.form.to_dict(flat=True)

    raw = request.get_data(as_text=True)
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            pass

    return {}


@api_bp.route('/public/services', methods=['GET'])
def public_services():
    archive_expired_pre_reservations()
    lang = _safe_lang(request.args.get('lang'))
    search = (request.args.get('q') or '').strip().lower()
    service_type = (request.args.get('type') or '').strip().lower()

    # Intento obtener de caché
    cache_key = f"public_services_{lang}_{search}_{service_type}"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    query = CampingService.query.filter_by(is_active=True)
    if service_type and service_type != 'all':
        query = query.filter(CampingService.service_type == service_type)

    services = query.order_by(CampingService.is_featured.desc(), CampingService.created_at.desc()).all()

    if search:
        services = [
            service for service in services
            if search in service.localized_name(lang).lower()
            or search in service.localized_description(lang).lower()
            or search in service.service_type.lower()
        ]

    result = [service.to_public_dict(lang) for service in services]
    
    # Guardar en caché por 5 minutos
    cache_service.set(cache_key, result, timeout=300)
    
    return jsonify(result)


@api_bp.route('/public/hero-images', methods=['GET'])
def public_hero_images():
    cache_key = "public_hero_images"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    images = HeroImage.query.filter_by(is_active=True).order_by(HeroImage.sort_order.asc(), HeroImage.id.asc()).all()
    result = [img.url for img in images]
    
    cache_service.set(cache_key, result, timeout=3600) # Cache por 1 hora
    return jsonify(result)


def _public_testimonials_response():
    lang = _safe_lang(request.args.get('lang'))
    service_id = request.args.get('service_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 8, type=int)
    
    cache_key = f"public_testimonios_{lang}_{service_id}_{page}_{per_page}"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        return jsonify(cached_data)

    query = ServiceTestimonial.query.filter_by(is_published=True)
    if service_id:
        query = query.filter_by(service_id=service_id)
        
    pagination = query.order_by(ServiceTestimonial.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    testimonials = [testimonial.to_public_dict(lang) for testimonial in pagination.items]
    result = {
        'testimonials': testimonials,
        'reviews': testimonials,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    }

    cache_service.set(cache_key, result, timeout=300)
    return jsonify(result)


@api_bp.route('/public/testimonios', methods=['GET'])
def public_testimonios():
    return _public_testimonials_response()


@api_bp.route('/public/reviews', methods=['GET'])
def public_reviews_alias():
    return _public_testimonials_response()


@api_bp.route('/public/pre-reservations', methods=['POST'])
def create_pre_reservation():
    archive_expired_pre_reservations()
    payload = _request_payload()
    form = PreReservationForm(formdata=MultiDict(payload))

    if not form.validate():
        return jsonify({'error': 'Datos inválidos', 'details': form.errors}), 400

    service = CampingService.query.filter_by(id=form.service_id.data, is_active=True).first()
    if not service:
        return jsonify({'error': 'Servicio no encontrado'}), 404

    if form.check_in.data >= form.check_out.data:
        return jsonify({'error': 'La fecha de salida debe ser posterior a la de ingreso'}), 400

    if form.guests.data > service.capacity:
        return jsonify({'error': 'La cantidad de huéspedes supera la capacidad del servicio'}), 400

    if service.available_units <= 0:
        return jsonify({'error': 'No hay disponibilidad para este servicio'}), 400

    reservation = PreReservation(
        code=_generate_pre_reservation_code(),
        service_id=service.id,
        full_name=form.full_name.data.strip(),
        email=form.email.data.strip().lower(),
        phone=form.phone.data.strip(),
        guests=form.guests.data,
        check_in=form.check_in.data,
        check_out=form.check_out.data,
        notes=(form.notes.data or '').strip(),
        lang=_safe_lang(form.lang.data),
        status='pendiente',
        source='web',
        confirmation_token=str(uuid.uuid4()),
        expires_at=datetime.utcnow() + timedelta(hours=48),
    )

    db.session.add(reservation)
    db.session.commit()

    send_camping_pre_reservation_email(reservation)

    return jsonify({
        'message': 'Pre-reserva registrada. Revisa tu email para los próximos pasos.',
        'code': reservation.code,
        'expires_at': reservation.expires_at.isoformat(),
    }), 201


@api_bp.route('/public/pre-reservations/confirm', methods=['GET'])
def confirm_public_pre_reservation():
    archive_expired_pre_reservations()
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Token requerido'}), 400

    reservation = PreReservation.query.filter_by(confirmation_token=token).first()
    if not reservation:
        return jsonify({'error': 'Token inválido'}), 404

    ok, message = confirm_pre_reservation(reservation)
    if not ok:
        return jsonify({'error': message, 'status': reservation.status}), 400

    return jsonify({'message': message, 'code': reservation.code}), 200


@api_bp.route('/public/suggestions', methods=['POST'])
def create_suggestion():
    payload = _request_payload()
    form = SuggestionForm(formdata=MultiDict(payload))
    if not form.validate():
        return jsonify({'error': 'Datos inválidos', 'details': form.errors}), 400

    suggestion = Suggestion(
        name=form.name.data.strip(),
        email=form.email.data.strip().lower(),
        category=form.category.data.strip().lower(),
        message=form.message.data.strip(),
        lang=_safe_lang(form.lang.data),
    )

    db.session.add(suggestion)
    db.session.commit()
    return jsonify({'message': 'Sugerencia registrada'}), 201


@api_bp.route('/public/health', methods=['GET'])
def public_health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})
