from datetime import datetime
from app.extensions import db
import json

class Locality(db.Model):
    __tablename__ = 'localities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    slots = db.relationship('AppointmentSlot', backref='locality', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='locality', lazy='dynamic')

    def __repr__(self):
        return f'<Locality {self.name}>'

class Procedure(db.Model):
    __tablename__ = 'procedures'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    requirements_json = db.Column(db.Text, nullable=True) # Stored as JSON string
    cost = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    slots = db.relationship('AppointmentSlot', backref='procedure', lazy='dynamic')
    reservations = db.relationship('Reservation', backref='procedure', lazy='dynamic')

    @property
    def requirements(self):
        if self.requirements_json:
            return json.loads(self.requirements_json)
        return []

    @requirements.setter
    def requirements(self, value):
        self.requirements_json = json.dumps(value)

    def __repr__(self):
        return f'<Procedure {self.name}>'

# Many-to-many relationship between Procedures and Localities
# (Which procedures are available in which localities)
procedure_localities = db.Table('procedure_localities',
    db.Column('procedure_id', db.Integer, db.ForeignKey('procedures.id'), primary_key=True),
    db.Column('locality_id', db.Integer, db.ForeignKey('localities.id'), primary_key=True)
)

class AppointmentSlot(db.Model):
    __tablename__ = 'appointment_slots'

    id = db.Column(db.Integer, primary_key=True)
    procedure_id = db.Column(db.Integer, db.ForeignKey('procedures.id'), nullable=False)
    locality_id = db.Column(db.Integer, db.ForeignKey('localities.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, default=1)
    current_bookings = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AppointmentSlot {self.date} {self.time} - Proc:{self.procedure_id} Loc:{self.locality_id}>'

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True) # Ej: ABC-123
    
    # User Data
    ci = db.Column(db.String(20), nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    
    # Details
    procedure_id = db.Column(db.Integer, db.ForeignKey('procedures.id'), nullable=False)
    locality_id = db.Column(db.Integer, db.ForeignKey('localities.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('appointment_slots.id'), nullable=False)
    
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    
    status = db.Column(db.String(20), default='pending') # pending, confirmed, cancelled, attended, expired
    source = db.Column(db.String(20), nullable=False, default='web', index=True) # web, admin
    confirmation_token = db.Column(db.String(100), unique=True, nullable=True)
    cancellation_token = db.Column(db.String(100), unique=True, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    slot = db.relationship('AppointmentSlot', backref=db.backref('reservations', lazy='dynamic'))

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "ci": self.ci,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "procedure": self.procedure.name if self.procedure else "Unknown",
            "locality": self.locality.name if self.locality else "Unknown",
            "date": self.date.isoformat(),
            "time": self.time.strftime('%H:%M'),
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Reservation {self.code} - {self.ci}>'
