from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app import bcrypt, db
from app.forms import UserForm
from app.models import User

bp = Blueprint('users', __name__)


def _parse_int(value):
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None

@bp.route('/users')
@login_required
def list_users():
    query = User.query
    search_term = (request.args.get('search') or '').strip()

    filters = {
        'user_code': (request.args.get('user_code') or '').strip(),
        'user_type': (request.args.get('user_type') or '').strip(),
        'user_birth_start': (request.args.get('user_birth_start') or '').strip(),
        'user_birth_end': (request.args.get('user_birth_end') or '').strip(),
        'user_phone': (request.args.get('user_phone') or '').strip(),
        'user_cpf': (request.args.get('user_cpf') or '').strip(),
        'user_rg': (request.args.get('user_rg') or '').strip(),
        'user_grade': (request.args.get('user_grade') or '').strip(),
        'user_class': (request.args.get('user_class') or '').strip(),
    }

    if search_term:
        query = query.filter(
            or_(
                User.userCompleteName.ilike(f"%{search_term}%"),
                User.identificationCode.ilike(f"%{search_term}%")
            )
        )

    if filters['user_code']:
        query = query.filter(User.identificationCode.ilike(f"%{filters['user_code']}%"))
    if filters['user_type']:
        query = query.filter(User.userType.ilike(f"%{filters['user_type']}%"))
    if filters['user_birth_start']:
        query = query.filter(User.birthDate >= filters['user_birth_start'])
    if filters['user_birth_end']:
        query = query.filter(User.birthDate <= filters['user_birth_end'])
    if filters['user_phone']:
        query = query.filter(User.userPhone.ilike(f"%{filters['user_phone']}%"))
    if filters['user_cpf']:
        query = query.filter(User.cpf.ilike(f"%{filters['user_cpf']}%"))
    if filters['user_rg']:
        query = query.filter(User.rg.ilike(f"%{filters['user_rg']}%"))
    grade = _parse_int(filters['user_grade'])
    if grade is not None:
        query = query.filter(User.gradeNumber == grade)
    if filters['user_class']:
        query = query.filter(User.className.ilike(f"%{filters['user_class']}%"))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    users = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('users.html', users=users, search_term=search_term, per_page=per_page, filters=filters)

@bp.route('/users/form', defaults={'user_id': None}, methods=['GET'])
@bp.route('/users/form/<int:user_id>', methods=['GET'])
@login_required
def get_user_form(user_id):
    if user_id:
        user = User.query.get_or_404(user_id)
        form = UserForm(obj=user, mode='edit', instance_id=user.userId)
    else:
        form = UserForm(mode='create')
    return render_template('_user_form.html', form=form, user_id=user_id)

@bp.route('/users/new', methods=['POST'])
@login_required
def new_user():
    form = UserForm(mode='create')
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') if form.password.data else bcrypt.generate_password_hash('123456').decode('utf-8')
        new_user = User(
            identificationCode=form.identificationCode.data.strip(),
            userCompleteName=form.userCompleteName.data.strip(),
            password=hashed_password,
            userType=form.userType.data,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
            userPhone=form.userPhone.data,
            birthDate=form.birthDate.data,
            cpf=form.cpf.data,
            rg=form.rg.data,
            gradeNumber=form.gradeNumber.data,
            className=form.className.data,
            guardianName1=form.guardianName1.data,
            guardianPhone1=form.guardianPhone1.data,
            guardianName2=form.guardianName2.data,
            guardianPhone2=form.guardianPhone2.data,
            notes=form.notes.data,
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})

@bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(request.form, obj=user, mode='edit', instance_id=user.userId)
    if form.validate():
        # manual populate to avoid overwriting id fields
        user.userType = form.userType.data
        user.identificationCode = form.identificationCode.data.strip()
        user.userCompleteName = form.userCompleteName.data.strip()
        user.userPhone = form.userPhone.data
        user.birthDate = form.birthDate.data
        user.cpf = form.cpf.data
        user.rg = form.rg.data
        user.gradeNumber = form.gradeNumber.data
        user.className = form.className.data
        user.guardianName1 = form.guardianName1.data
        user.guardianPhone1 = form.guardianPhone1.data
        user.guardianName2 = form.guardianName2.data
        user.guardianPhone2 = form.guardianPhone2.data
        user.notes = form.notes.data
        if form.password.data:
            user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.lastUpdate = date.today()
        user.updatedBy = current_user.userId
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})

@bp.route('/users/check-identification', methods=['GET'])
@login_required
def check_identification_code():
    code = (request.args.get('code') or '').strip()
    exists = False
    if code:
        exists = db.session.query(User.userId).filter_by(identificationCode=code).first() is not None
    return jsonify({'exists': exists})

@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('users.list_users'))


# Configuration Management Routes

