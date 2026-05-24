from datetime import datetime
from app import db


class DirectorySubmission(db.Model):
    __tablename__ = 'directory_submissions'

    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    directory_name = db.Column(db.String(255), nullable=False)
    directory_url = db.Column(db.String(500))
    submission_url = db.Column(db.String(500))
    guide_url = db.Column(db.String(1024))
    screenshot_path = db.Column(db.String(500), nullable=True)
    status = db.Column(
        db.String(20),
        default='pending',
        comment='pending, in_progress, completed, failed, skipped, manual'
    )
    error_message = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    captcha_detected = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'business_id': self.business_id,
            'directory_name': self.directory_name,
            'directory_url': self.directory_url,
            'submission_url': self.submission_url,
            'guide_url': self.guide_url,
            'screenshot_path': self.screenshot_path,
            'status': self.status,
            'error_message': self.error_message,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'captcha_detected': self.captcha_detected,
        }

    def __repr__(self):
        return f'<DirectorySubmission {self.id}: {self.directory_name} ({self.status})>'
