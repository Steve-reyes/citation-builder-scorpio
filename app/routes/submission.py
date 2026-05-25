import json
import threading
from datetime import datetime
from sqlalchemy import or_
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app import create_app, db
from app.config import Config
from app.models.business import Business
from app.models.submission import DirectorySubmission
from app.services.submission_engine import SubmissionEngine

submission_bp = Blueprint('submission', __name__)

# Keep a reference to running tasks
_submission_tasks = {}


def load_directories():
    """Load directories from the JSON data file."""
    try:
        with open(Config.DIRECTORIES_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('directories', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@submission_bp.route('/submissions')
def list_submissions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', '')
    directory_filter = request.args.get('directory', '')

    query = DirectorySubmission.query

    if status_filter:
        query = query.filter(DirectorySubmission.status == status_filter)
    if directory_filter:
        query = query.filter(DirectorySubmission.directory_name.ilike(f'%{directory_filter}%'))

    query = query.order_by(DirectorySubmission.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'submission/list.html',
        submissions=pagination.items,
        pagination=pagination,
        status_filter=status_filter,
        directory_filter=directory_filter,
    )


@submission_bp.route('/businesses/<int:id>/submit')
def submit_page(id):
    business = Business.query.get_or_404(id)
    directories = load_directories()
    existing = {
        s.directory_name: s.status
        for s in DirectorySubmission.query.filter_by(business_id=id).all()
    }
    return render_template(
        'submission/submit.html',
        business=business,
        directories=directories,
        existing=existing,
    )


def run_batch_submission(app, business_id, directories_subset=None):
    """Run batch submission in a background thread."""
    with app.app_context():
        business = Business.query.get(business_id)
        if not business:
            return

        engine = SubmissionEngine()
        engine.batch_submit(business, directories_subset=directories_subset)


@submission_bp.route('/businesses/<int:id>/start', methods=['POST'])
def start_submission(id):
    business = Business.query.get_or_404(id)

    # Create submission records for all directories
    directories = load_directories()
    directory_names_param = request.form.get('directories', '')

    if directory_names_param:
        selected_names = [n.strip() for n in directory_names_param.split(',') if n.strip()]
        dirs_to_submit = [d for d in directories if d['name'] in selected_names]
    else:
        dirs_to_submit = directories

    created_count = 0
    for directory in dirs_to_submit:
        existing = DirectorySubmission.query.filter_by(
            business_id=business.id,
            directory_name=directory['name'],
        ).first()

        if existing and existing.status in ('completed', 'in_progress'):
            continue

        if existing:
            existing.status = 'pending'
            existing.error_message = None
            existing.captcha_detected = False
        else:
            sub = DirectorySubmission(
                business_id=business.id,
                directory_name=directory['name'],
                directory_url=directory.get('url', ''),
                submission_url=directory.get('submission_url', ''),
                status='pending',
            )
            db.session.add(sub)
        created_count += 1

    db.session.commit()

    # Start background thread
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=run_batch_submission,
        args=(app, business.id, dirs_to_submit),
        daemon=True,
    )
    thread.start()

    flash(
        f'Batch submission started for {created_count} directories on "{business.business_name}".',
        'success',
    )
    return redirect(url_for('submission.batch_progress', id=business.id))


@submission_bp.route('/businesses/<int:id>/batch-progress')
def batch_progress(id):
    business = Business.query.get_or_404(id)
    submissions = DirectorySubmission.query.filter_by(business_id=id).order_by(
        DirectorySubmission.created_at.asc()
    ).all()

    total = len(submissions)
    done = sum(1 for s in submissions if s.status in ('completed', 'failed', 'skipped'))
    stats = {
        'total': total,
        'completed': sum(1 for s in submissions if s.status == 'completed'),
        'failed': sum(1 for s in submissions if s.status == 'failed'),
        'in_progress': sum(1 for s in submissions if s.status == 'in_progress'),
        'pending': sum(1 for s in submissions if s.status == 'pending'),
        'skipped': sum(1 for s in submissions if s.status == 'skipped'),
        'manual': sum(1 for s in submissions if s.status == 'manual'),
        'batch_complete': total > 0 and done == total,
    }

    return render_template(
        'submission/batch_progress.html',
        business=business,
        submissions=submissions,
        stats=stats,
    )


@submission_bp.route('/api/submissions/<int:business_id>')
def api_submission_status(business_id):
    business = Business.query.get_or_404(business_id)
    submissions = DirectorySubmission.query.filter_by(business_id=business_id).order_by(
        DirectorySubmission.created_at.desc()
    ).all()

    stats = {
        'total': len(submissions),
        'completed': sum(1 for s in submissions if s.status == 'completed'),
        'failed': sum(1 for s in submissions if s.status == 'failed'),
        'pending': sum(1 for s in submissions if s.status == 'pending'),
        'in_progress': sum(1 for s in submissions if s.status == 'in_progress'),
        'skipped': sum(1 for s in submissions if s.status == 'skipped'),
        'captcha': sum(1 for s in submissions if s.captcha_detected),
        'manual': sum(1 for s in submissions if s.status == 'manual'),
        'batch_complete': len(submissions) > 0 and all(
            s.status in ('completed', 'failed', 'skipped')
            for s in submissions
        ),
    }

    return jsonify({
        'business': business.to_dict(),
        'stats': stats,
        'submissions': [s.to_dict() for s in submissions],
    })


@submission_bp.route('/submissions/<int:id>/retry', methods=['POST'])
def retry_submission(id):
    submission = DirectorySubmission.query.get_or_404(id)
    submission.status = 'pending'
    submission.error_message = None
    submission.captcha_detected = False
    db.session.commit()

    # Start a single-directory submission in background
    business = Business.query.get(submission.business_id)
    if business:
        directories = load_directories()
        directory = next((d for d in directories if d['name'] == submission.directory_name), None)
        if directory:
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=_run_single_submission,
                args=(app, business.id, directory),
                daemon=True,
            )
            thread.start()

    flash(f'Retry queued for "{submission.directory_name}".', 'info')
    return redirect(url_for('business.view_business', id=submission.business_id))


def _run_single_submission(app, business_id, directory):
    """Run a single directory submission in background."""
    with app.app_context():
        business = Business.query.get(business_id)
        if not business:
            return
        engine = SubmissionEngine()
        engine.submit_business_to_directory(business, directory)


@submission_bp.route('/submissions/<int:id>/skip', methods=['POST'])
def skip_submission(id):
    submission = DirectorySubmission.query.get_or_404(id)
    submission.status = 'skipped'
    submission.error_message = 'Manually skipped by user.'
    db.session.commit()
    flash(f'Skipped submission for "{submission.directory_name}".', 'warning')
    return redirect(url_for('business.view_business', id=submission.business_id))


@submission_bp.route('/captcha-queue')
def captcha_queue():
    """Show all submissions with CAPTCHA detected (manual or captcha_detected)."""
    page = request.args.get('page', 1, type=int)
    per_page = 25

    query = DirectorySubmission.query.filter(
        or_(
            DirectorySubmission.captcha_detected == True,
            DirectorySubmission.status == 'manual',
        )
    ).order_by(DirectorySubmission.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    submissions = pagination.items

    return render_template(
        'submission/captcha_queue.html',
        submissions=submissions,
        pagination=pagination,
    )
