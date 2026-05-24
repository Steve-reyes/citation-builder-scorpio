from flask import Blueprint, render_template, jsonify
from app import db
from app.models.business import Business
from app.models.submission import DirectorySubmission

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    total_businesses = Business.query.count()
    total_submissions = DirectorySubmission.query.count()
    completed = DirectorySubmission.query.filter_by(status='completed').count()
    failed = DirectorySubmission.query.filter_by(status='failed').count()
    pending = DirectorySubmission.query.filter_by(status='pending').count()
    in_progress = DirectorySubmission.query.filter_by(status='in_progress').count()
    success_rate = round((completed / total_submissions * 100), 1) if total_submissions > 0 else 0
    captcha_count = DirectorySubmission.query.filter_by(captcha_detected=True).count()

    return render_template(
        'dashboard/index.html',
        total_businesses=total_businesses,
        total_submissions=total_submissions,
        completed=completed,
        failed=failed,
        pending=pending,
        in_progress=in_progress,
        success_rate=success_rate,
        captcha_count=captcha_count,
    )


@dashboard_bp.route('/api/stats')
def api_stats():
    total_businesses = Business.query.count()
    total_submissions = DirectorySubmission.query.count()
    completed = DirectorySubmission.query.filter_by(status='completed').count()
    failed = DirectorySubmission.query.filter_by(status='failed').count()
    pending = DirectorySubmission.query.filter_by(status='pending').count()
    in_progress = DirectorySubmission.query.filter_by(status='in_progress').count()
    skipped = DirectorySubmission.query.filter_by(status='skipped').count()
    success_rate = round((completed / total_submissions * 100), 1) if total_submissions > 0 else 0
    captcha_count = DirectorySubmission.query.filter_by(captcha_detected=True).count()

    return jsonify({
        'total_businesses': total_businesses,
        'total_submissions': total_submissions,
        'completed': completed,
        'failed': failed,
        'pending': pending,
        'in_progress': in_progress,
        'skipped': skipped,
        'success_rate': success_rate,
        'captcha_detected': captcha_count,
    })
