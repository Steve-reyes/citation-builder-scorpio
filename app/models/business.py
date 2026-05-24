from datetime import datetime
from app import db


class Business(db.Model):
    __tablename__ = 'businesses'

    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    province = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    website = db.Column(db.String(500))
    email = db.Column(db.String(255))
    description = db.Column(db.Text)
    categories = db.Column(db.String(500), comment='Comma-separated categories')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='draft', comment='draft, active, paused')

    submissions = db.relationship(
        'DirectorySubmission',
        backref='business',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'website': self.website,
            'email': self.email,
            'description': self.description,
            'categories': self.categories,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
        }

    def __repr__(self):
        return f'<Business {self.id}: {self.business_name}>'
