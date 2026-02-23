from datetime import datetime
from app.extensions import db

# Association table for CampingService and Amenity
service_amenities = db.Table('service_amenities',
    db.Column('service_id', db.Integer, db.ForeignKey('camping_services.id'), primary_key=True),
    db.Column('amenity_id', db.Integer, db.ForeignKey('amenities.id'), primary_key=True)
)

class CampingService(db.Model):
    __tablename__ = 'camping_services'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    service_type = db.Column(db.String(30), nullable=False, index=True)

    name_es = db.Column(db.String(160), nullable=False)
    name_en = db.Column(db.String(160), nullable=False)
    name_pt = db.Column(db.String(160), nullable=False)

    description_es = db.Column(db.Text, nullable=False)
    description_en = db.Column(db.Text, nullable=False)
    description_pt = db.Column(db.Text, nullable=False)

    price = db.Column(db.Integer, nullable=False, default=0)
    currency = db.Column(db.String(8), nullable=False, default='UYU')
    capacity = db.Column(db.Integer, nullable=False, default=1)
    total_units = db.Column(db.Integer, nullable=False, default=0)
    available_units = db.Column(db.Integer, nullable=False, default=0)

    rating_avg = db.Column(db.Float, nullable=False, default=0)
    rating_count = db.Column(db.Integer, nullable=False, default=0)

    is_featured = db.Column(db.Boolean, default=False)
    is_promo = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = db.relationship('ServiceImage', backref='service', cascade='all, delete-orphan', lazy='dynamic')
    testimonials = db.relationship('ServiceTestimonial', backref='service', cascade='all, delete-orphan', lazy='dynamic')
    pre_reservations = db.relationship('PreReservation', backref='service', lazy='dynamic')
    
    amenities = db.relationship('Amenity', secondary=service_amenities, backref=db.backref('services', lazy='dynamic'))

    def localized_name(self, lang='es'):
        if lang == 'en':
            return self.name_en
        if lang == 'pt':
            return self.name_pt
        return self.name_es

    def localized_description(self, lang='es'):
        if lang == 'en':
            return self.description_en
        if lang == 'pt':
            return self.description_pt
        return self.description_es

    def to_public_dict(self, lang='es'):
        ordered_images = self.images.order_by(ServiceImage.sort_order.asc(), ServiceImage.id.asc()).all()
        return {
            'id': self.id,
            'slug': self.slug,
            'type': self.service_type,
            'name': self.localized_name(lang),
            'description': self.localized_description(lang),
            'price': self.price,
            'currency': self.currency,
            'capacity': self.capacity,
            'total': self.total_units,
            'available': self.available_units,
            'featured': self.is_featured,
            'promo': self.is_promo,
            'amenities': [a.to_dict(lang) for a in self.amenities],
            'images': [img.url for img in ordered_images],
        }


class Amenity(db.Model):
    __tablename__ = 'amenities'

    id = db.Column(db.Integer, primary_key=True)
    name_es = db.Column(db.String(100), nullable=False)
    name_en = db.Column(db.String(100), nullable=True)
    name_pt = db.Column(db.String(100), nullable=True)
    icon = db.Column(db.String(20), nullable=False)  # Emoji icon
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, lang=None):
        if lang:
            name = self.name_es
            if lang == 'en' and self.name_en:
                name = self.name_en
            elif lang == 'pt' and self.name_pt:
                name = self.name_pt
                
            return {
                'id': self.id,
                'name': name,
                'icon': self.icon
            }
        
        # Admin full dict
        return {
            'id': self.id,
            'name_es': self.name_es,
            'name_en': self.name_en,
            'name_pt': self.name_pt,
            'icon': self.icon
        }

class ServiceImage(db.Model):
    __tablename__ = 'service_images'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('camping_services.id'), nullable=False, index=True)
    url = db.Column(db.String(512), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class HeroImage(db.Model):
    __tablename__ = 'hero_images'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ServiceTestimonial(db.Model):
    __tablename__ = 'service_reviews'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('camping_services.id'), nullable=True, index=True)
    author_name = db.Column(db.String(120), nullable=False)
    rating = db.Column(db.Integer, nullable=False, default=0)
    comment_es = db.Column(db.Text, nullable=False)
    comment_en = db.Column(db.Text, nullable=False)
    comment_pt = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(512), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def localized_comment(self, lang='es'):
        if lang == 'en':
            return self.comment_en
        if lang == 'pt':
            return self.comment_pt
        return self.comment_es

    def to_public_dict(self, lang='es'):
        return {
            'id': self.id,
            'author_name': self.author_name,
            'message': self.localized_comment(lang),
            'created_at': self.created_at.date().isoformat() if self.created_at else None,
            'is_approved': self.is_published,
            'image_url': self.image_url,
            'service_name': self.service.localized_name(lang) if self.service else '',
        }


class PreReservation(db.Model):
    __tablename__ = 'pre_reservations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(24), unique=True, nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('camping_services.id'), nullable=False, index=True)

    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(140), nullable=False, index=True)
    phone = db.Column(db.String(40), nullable=False)
    guests = db.Column(db.Integer, nullable=False, default=1)

    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    lang = db.Column(db.String(5), nullable=False, default='es')

    status = db.Column(db.String(30), nullable=False, default='pendiente', index=True)
    source = db.Column(db.String(20), nullable=False, default='web', index=True)
    archive_reason = db.Column(db.Text, nullable=True)
    confirmation_token = db.Column(db.String(128), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    confirmed_at = db.Column(db.DateTime, nullable=True)
    checked_in_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_admin_dict(self):
        status_map = {
            'pendiente': 'PENDIENTE',
            'confirmado': 'CONFIRMADO',
            'activo': 'ACTIVO',
            'completado': 'COMPLETADO',
            'expirado': 'EXPIRADO',
            'archivado_admin': 'ARCHIVADO (ADMIN)'
        }
        return {
            'id': self.id,
            'code': self.code,
            'service': self.service.localized_name(self.lang) if self.service else 'N/A',
            'source': self.source,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'guests': self.guests,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'status': self.status,
            'status_label': status_map.get(self.status, self.status.upper()),
            'archive_reason': self.archive_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


class Suggestion(db.Model):
    __tablename__ = 'suggestions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(140), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    lang = db.Column(db.String(5), nullable=False, default='es')
    status = db.Column(db.String(30), nullable=False, default='nuevo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def category_label(self):
        category_map = {
            'general': 'General',
            'services': 'Servicios',
            'facilities': 'Instalaciones',
            'activities': 'Actividades'
        }
        return category_map.get(self.category, self.category.capitalize())

    def to_dict(self):
        status_map = {
            'nuevo': 'NUEVO',
            'revisado': 'REVISADO',
            'archivado': 'ARCHIVADO'
        }
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'category': self.category,
            'category_label': self.category_label.upper(),
            'message': self.message,
            'lang': self.lang.upper(),
            'status_label': status_map.get(self.status, self.status.upper()),
            'status_raw': self.status,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else ''
        }


class MediaAsset(db.Model):
    __tablename__ = 'media_assets'

    id = db.Column(db.Integer, primary_key=True)
    object_name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    url = db.Column(db.String(512), nullable=False)
    mime_type = db.Column(db.String(120), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    usage_type = db.Column(db.String(40), nullable=False)
    reference_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
