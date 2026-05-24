from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.business import Business
from app.models.submission import DirectorySubmission

business_bp = Blueprint('business', __name__)


@business_bp.route('/businesses')
def list_businesses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Business.query

    if status_filter:
        query = query.filter(Business.status == status_filter)
    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                Business.business_name.ilike(like),
                Business.city.ilike(like),
                Business.province.ilike(like),
                Business.email.ilike(like),
            )
        )

    query = query.order_by(Business.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    businesses = pagination.items

    return render_template(
        'business/list.html',
        businesses=businesses,
        pagination=pagination,
        status_filter=status_filter,
        search=search,
    )


@business_bp.route('/businesses/new', methods=['GET', 'POST'])
def create_business():
    if request.method == 'POST':
        business = Business(
            business_name=request.form.get('business_name', '').strip(),
            phone=request.form.get('phone', '').strip(),
            address=request.form.get('address', '').strip(),
            city=request.form.get('city', '').strip(),
            province=request.form.get('province', '').strip(),
            postal_code=request.form.get('postal_code', '').strip(),
            website=request.form.get('website', '').strip(),
            email=request.form.get('email', '').strip(),
            description=request.form.get('description', '').strip(),
            categories=request.form.get('categories', '').strip(),
            status=request.form.get('status', 'draft'),
        )

        if not business.business_name:
            flash('Business name is required.', 'danger')
            return render_template('business/create.html')

        db.session.add(business)
        db.session.commit()
        flash(f'Business "{business.business_name}" created successfully.', 'success')
        return redirect(url_for('business.view_business', id=business.id))

    return render_template('business/create.html')


@business_bp.route('/businesses/<int:id>')
def view_business(id):
    business = Business.query.get_or_404(id)
    submissions = DirectorySubmission.query.filter_by(business_id=id).order_by(
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
    }

    return render_template(
        'business/view.html',
        business=business,
        submissions=submissions,
        stats=stats,
    )


@business_bp.route('/businesses/<int:id>/edit', methods=['GET', 'POST'])
def edit_business(id):
    business = Business.query.get_or_404(id)

    if request.method == 'POST':
        business.business_name = request.form.get('business_name', '').strip()
        business.phone = request.form.get('phone', '').strip()
        business.address = request.form.get('address', '').strip()
        business.city = request.form.get('city', '').strip()
        business.province = request.form.get('province', '').strip()
        business.postal_code = request.form.get('postal_code', '').strip()
        business.website = request.form.get('website', '').strip()
        business.email = request.form.get('email', '').strip()
        business.description = request.form.get('description', '').strip()
        business.categories = request.form.get('categories', '').strip()
        business.status = request.form.get('status', 'draft')
        business.updated_at = datetime.utcnow()

        if not business.business_name:
            flash('Business name is required.', 'danger')
            return render_template('business/edit.html', business=business)

        db.session.commit()
        flash(f'Business "{business.business_name}" updated.', 'success')
        return redirect(url_for('business.view_business', id=business.id))

    return render_template('business/edit.html', business=business)


@business_bp.route('/businesses/<int:id>/delete', methods=['POST'])
def delete_business(id):
    business = Business.query.get_or_404(id)
    name = business.business_name
    db.session.delete(business)
    db.session.commit()
    flash(f'Business "{name}" deleted.', 'info')
    return redirect(url_for('business.list_businesses'))


@business_bp.route('/api/businesses')
def api_list_businesses():
    businesses = Business.query.order_by(Business.updated_at.desc()).all()
    return jsonify([b.to_dict() for b in businesses])


@business_bp.route('/api/businesses/<int:id>')
def api_get_business(id):
    business = Business.query.get_or_404(id)
    return jsonify(business.to_dict())
