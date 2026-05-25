import json
import os
from datetime import datetime, timedelta

from flask import Blueprint, render_template, jsonify
from sqlalchemy import func

from app import db
from app.models.business import Business
from app.models.submission import DirectorySubmission

dashboard_bp = Blueprint('dashboard', __name__)

# ── helpers ──────────────────────────────────────────────────────────

def _load_directory_difficulties():
    """Return a dict mapping directory name -> difficulty (easy/medium/hard)."""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'data', 'ca_directories.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = json.load(f)
    return {entry['name']: entry.get('difficulty', 'medium')
            for entry in data.get('directories', [])}


def _get_date_range(days=14):
    """Return list of the last N date strings (YYYY-MM-DD)."""
    today = datetime.utcnow().date()
    return [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]


def _get_by_difficulty(difficulty_map, status='completed'):
    """Return a dict {difficulty: count} for a given status."""
    result = {'easy': 0, 'medium': 0, 'hard': 0}
    rows = DirectorySubmission.query.with_entities(
        DirectorySubmission.directory_name,
        func.count().label('cnt')
    ).filter(DirectorySubmission.status == status).group_by(
        DirectorySubmission.directory_name).all()
    for name, cnt in rows:
        diff = difficulty_map.get(name, 'medium')
        if diff not in result:
            result[diff] = 0
        result[diff] += cnt
    return result

# ── routes ───────────────────────────────────────────────────────────

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


@dashboard_bp.route('/analytics')
def analytics():
    """Analytics dashboard with charts."""
    # ── aggregates ────────────────────────────────────────────────
    total = DirectorySubmission.query.count()
    completed = DirectorySubmission.query.filter_by(status='completed').count()
    failed = DirectorySubmission.query.filter_by(status='failed').count()
    manual = DirectorySubmission.query.filter_by(status='manual').count()
    pending = DirectorySubmission.query.filter_by(status='pending').count()
    skipped = DirectorySubmission.query.filter_by(status='skipped').count()
    in_progress = DirectorySubmission.query.filter_by(status='in_progress').count()
    success_rate = round((completed / total * 100), 1) if total > 0 else 0
    captcha_count = DirectorySubmission.query.filter_by(captcha_detected=True).count()
    total_businesses = Business.query.count()
    avg_per_business = round(total / total_businesses, 1) if total_businesses > 0 else 0

    # ── status breakdown (ready for donut chart) ──────────────────
    status_labels = ['completed', 'failed', 'manual', 'pending', 'skipped']
    status_counts = [completed, failed, manual, pending, skipped]

    # ── daily submissions (last 14 days) ──────────────────────────
    date_range = _get_date_range(14)
    date_str = func.strftime('%Y-%m-%d', DirectorySubmission.submitted_at)
    daily_rows = DirectorySubmission.query.with_entities(
        date_str,
        func.count().label('cnt')
    ).filter(
        DirectorySubmission.submitted_at.isnot(None),
        DirectorySubmission.submitted_at >= (datetime.utcnow() - timedelta(days=14))
    ).group_by(date_str).order_by(date_str).all()
    daily_map = {str(r[0]): r[1] for r in daily_rows}
    daily_counts = [daily_map.get(d, 0) for d in date_range]

    # ── difficulty performance ────────────────────────────────────
    difficulty_map = _load_directory_difficulties()
    diff_completed = _get_by_difficulty(difficulty_map, 'completed')
    diff_total = {
        'easy': 0,
        'medium': 0,
        'hard': 0,
    }
    all_rows = DirectorySubmission.query.with_entities(
        DirectorySubmission.directory_name,
        func.count().label('cnt')
    ).group_by(DirectorySubmission.directory_name).all()
    for name, cnt in all_rows:
        diff = difficulty_map.get(name, 'medium')
        if diff not in diff_total:
            diff_total[diff] = 0
        diff_total[diff] += cnt
    _sum = lambda d: sum(d.values()) or 1
    diff_rate = {}
    for key in ('easy', 'medium', 'hard'):
        total_for_diff = diff_total.get(key, 0)
        completed_for_diff = diff_completed.get(key, 0)
        diff_rate[key] = {
            'completed': completed_for_diff,
            'total': total_for_diff,
            'rate': round(completed_for_diff / total_for_diff * 100, 1) if total_for_diff > 0 else 0,
        }

    # ── top 10 directories (by completed count) ───────────────────
    top_dirs = DirectorySubmission.query.with_entities(
        DirectorySubmission.directory_name,
        func.count().label('cnt')
    ).filter(DirectorySubmission.status == 'completed').group_by(
        DirectorySubmission.directory_name
    ).order_by(func.count().desc()).limit(10).all()

    # ── top 10 worst directories (by failed count) ────────────────
    worst_dirs = DirectorySubmission.query.with_entities(
        DirectorySubmission.directory_name,
        func.count().label('cnt')
    ).filter(DirectorySubmission.status == 'failed').group_by(
        DirectorySubmission.directory_name
    ).order_by(func.count().desc()).limit(10).all()

    return render_template(
        'dashboard/analytics.html',
        total=total,
        completed=completed,
        failed=failed,
        manual=manual,
        pending=pending,
        skipped=skipped,
        in_progress=in_progress,
        success_rate=success_rate,
        captcha_count=captcha_count,
        total_businesses=total_businesses,
        avg_per_business=avg_per_business,
        # chart data
        status_labels=status_labels,
        status_counts=status_counts,
        date_range=date_range,
        daily_counts=daily_counts,
        diff_rate=diff_rate,
        top_dirs=top_dirs,
        worst_dirs=worst_dirs,
    )
