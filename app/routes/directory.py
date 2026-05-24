import json
from flask import Blueprint, render_template, request, jsonify
from app import db
from app.config import Config

directory_bp = Blueprint('directory', __name__)


def load_directories():
    """Load directories from the JSON data file."""
    try:
        with open(Config.DIRECTORIES_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('directories', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return []


@directory_bp.route('/directories')
def list_directories():
    directories = load_directories()
    province_filter = request.args.get('province', '')
    category_filter = request.args.get('category', '')
    difficulty_filter = request.args.get('difficulty', '')
    search = request.args.get('search', '')

    if province_filter:
        directories = [
            d for d in directories
            if not d.get('province_focus') or province_filter in d['province_focus']
        ]
    if category_filter:
        directories = [d for d in directories if d.get('category') == category_filter]
    if difficulty_filter:
        directories = [d for d in directories if d.get('difficulty') == difficulty_filter]
    if search:
        q = search.lower()
        directories = [
            d for d in directories
            if q in d.get('name', '').lower()
        ]

    # Extract distinct values for filter controls
    all_dirs = load_directories()
    provinces = sorted(set(
        p for d in all_dirs for p in d.get('province_focus', [])
    ))
    categories = sorted(set(d.get('category', '') for d in all_dirs if d.get('category')))
    difficulties = sorted(set(d.get('difficulty', '') for d in all_dirs if d.get('difficulty')))

    return render_template(
        'directory/list.html',
        directories=directories,
        provinces=provinces,
        categories=categories,
        difficulties=difficulties,
        province_filter=province_filter,
        category_filter=category_filter,
        difficulty_filter=difficulty_filter,
        search=search,
        total=len(directories),
    )


@directory_bp.route('/api/directories')
def api_list_directories():
    directories = load_directories()
    province_filter = request.args.get('province', '')
    category_filter = request.args.get('category', '')
    difficulty_filter = request.args.get('difficulty', '')
    search = request.args.get('search', '')

    if province_filter:
        directories = [
            d for d in directories
            if not d.get('province_focus') or province_filter in d['province_focus']
        ]
    if category_filter:
        directories = [d for d in directories if d.get('category') == category_filter]
    if difficulty_filter:
        directories = [d for d in directories if d.get('difficulty') == difficulty_filter]
    if search:
        q = search.lower()
        directories = [
            d for d in directories
            if q in d.get('name', '').lower()
        ]

    return jsonify(directories)


@directory_bp.route('/api/directories/by_province/<province>')
def api_directories_by_province(province):
    directories = load_directories()
    filtered = [
        d for d in directories
        if not d.get('province_focus') or province in d['province_focus']
    ]
    return jsonify(filtered)
