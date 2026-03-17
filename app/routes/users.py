from datetime import date
import io
import os
import threading

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app import bcrypt, db
from app.forms import UserForm
from app.models import User
from app.services import (
    USER_BULK_TEMPLATE_COLUMNS,
    build_user_bulk_template_rows,
    create_job,
    get_job,
    get_bulk_field_label,
    get_required_fields_for_user_type,
    run_user_create_import_job,
)
from app.utils import SUPPORTED_IMPORT_EXTENSIONS, build_template_bytes, can_manage_user_bulk_import, detect_extension

bp = Blueprint('users', __name__)

ALLOWED_BULK_USER_TYPES = [
    ('aluno', 'Aluno'),
    ('colaborador', 'Colaborador'),
    ('bibliotecario', 'Bibliotecário'),
    ('admin', 'Admin'),
]


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
            pcd=bool(form.pcd.data),
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
        user.pcd = bool(form.pcd.data)
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


def _ensure_bulk_import_permission():
    if not can_manage_user_bulk_import():
        flash('Acesso negado. Somente admin e bibliotecário podem importar usuários em massa.', 'warning')
        return False
    return True


def _is_valid_bulk_user_type(user_type: str) -> bool:
    return user_type in {item[0] for item in ALLOWED_BULK_USER_TYPES}


def _is_job_owner_or_allowed(job_data: dict) -> bool:
    if not job_data:
        return False
    if current_user.userId == job_data.get('ownerUserId'):
        return True
    return can_manage_user_bulk_import()


@bp.route('/users/import/bulk', methods=['GET', 'POST'])
@login_required
def bulk_user_import_select_type():
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    if request.method == 'POST':
        selected_user_type = (request.form.get('user_type') or request.form.get('userType') or '').strip().lower()
        if not _is_valid_bulk_user_type(selected_user_type):
            flash('Tipo de usuário inválido para importação.', 'danger')
            return render_template('users_bulk_import_type.html', user_types=ALLOWED_BULK_USER_TYPES)

        return redirect(url_for('users.bulk_user_import_upload', user_type=selected_user_type))

    return render_template('users_bulk_import_type.html', user_types=ALLOWED_BULK_USER_TYPES)


@bp.route('/users/import/bulk/upload', methods=['GET', 'POST'])
@login_required
def bulk_user_import_upload():
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    selected_user_type = (request.args.get('user_type') or request.form.get('user_type') or '').strip().lower()
    if not _is_valid_bulk_user_type(selected_user_type):
        flash('Selecione um tipo de usuário válido antes de enviar o arquivo.', 'warning')
        return redirect(url_for('users.bulk_user_import_select_type'))

    if request.method == 'POST':
        upload_file = request.files.get('importFile')
        if not upload_file or not upload_file.filename:
            flash('Selecione um arquivo CSV ou XLSX para continuar.', 'danger')
            return render_template('users_bulk_import_upload.html', selected_user_type=selected_user_type)

        extension = detect_extension(upload_file.filename)
        if extension not in SUPPORTED_IMPORT_EXTENSIONS:
            flash('Formato de arquivo inválido. Use CSV ou XLSX.', 'danger')
            return render_template('users_bulk_import_upload.html', selected_user_type=selected_user_type)

        jobs_root = os.path.join(current_app.instance_path, 'bulk_import_jobs')
        uploads_root = os.path.join(jobs_root, 'uploads')
        errors_root = os.path.join(jobs_root, 'errors')
        os.makedirs(uploads_root, exist_ok=True)
        os.makedirs(errors_root, exist_ok=True)

        job_id = create_job(
            owner_user_id=current_user.userId,
            kind='user_bulk_create',
            metadata={
                'selectedUserType': selected_user_type,
                'originalFilename': upload_file.filename,
            },
        )

        source_path = os.path.join(uploads_root, f'{job_id}.{extension}')
        error_report_path = os.path.join(errors_root, f'{job_id}_erros.xlsx')
        upload_file.save(source_path)

        app_obj = current_app._get_current_object()
        worker = threading.Thread(
            target=run_user_create_import_job,
            args=(
                app_obj,
                job_id,
                source_path,
                extension,
                selected_user_type,
                current_user.userId,
                error_report_path,
            ),
            daemon=True,
        )
        worker.start()

        return redirect(url_for('users.bulk_user_import_progress', job_id=job_id))

    required_fields = get_required_fields_for_user_type(selected_user_type)
    required_fields_display = [get_bulk_field_label(field_name) for field_name in required_fields]
    return render_template(
        'users_bulk_import_upload.html',
        selected_user_type=selected_user_type,
        required_fields=required_fields_display,
    )


@bp.route('/users/import/bulk/template', methods=['GET'])
@login_required
def bulk_user_import_download_template():
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    selected_user_type = (request.args.get('user_type') or request.args.get('userType') or '').strip().lower()
    output_format = (request.args.get('format') or 'xlsx').strip().lower()

    if not _is_valid_bulk_user_type(selected_user_type):
        flash('Selecione um tipo de usuário válido para baixar o modelo.', 'warning')
        return redirect(url_for('users.bulk_user_import_select_type'))

    if output_format not in SUPPORTED_IMPORT_EXTENSIONS:
        flash('Formato inválido. Use CSV ou XLSX.', 'warning')
        return redirect(url_for('users.bulk_user_import_upload', user_type=selected_user_type))

    headers = list(USER_BULK_TEMPLATE_COLUMNS)
    sample_rows = build_user_bulk_template_rows(selected_user_type)
    content = build_template_bytes(output_format, headers, sample_rows)

    mimetype = 'text/csv; charset=utf-8' if output_format == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(
        io.BytesIO(content),
        as_attachment=True,
        download_name=f'modelo_importacao_usuarios_{selected_user_type}.{output_format}',
        mimetype=mimetype,
    )


@bp.route('/users/import/bulk/progress/<job_id>', methods=['GET'])
@login_required
def bulk_user_import_progress(job_id):
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    job_data = get_job(job_id)
    if not _is_job_owner_or_allowed(job_data):
        abort(404)

    return render_template('users_bulk_import_progress.html', job_id=job_id)


@bp.route('/users/import/bulk/status/<job_id>', methods=['GET'])
@login_required
def bulk_user_import_status(job_id):
    if not _ensure_bulk_import_permission():
        return jsonify({'success': False, 'error': 'Acesso negado.'}), 403

    job_data = get_job(job_id)
    if not _is_job_owner_or_allowed(job_data):
        return jsonify({'success': False, 'error': 'Job não encontrado.'}), 404

    return jsonify({'success': True, 'job': job_data})


@bp.route('/users/import/bulk/result/<job_id>', methods=['GET'])
@login_required
def bulk_user_import_result(job_id):
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    job_data = get_job(job_id)
    if not _is_job_owner_or_allowed(job_data):
        abort(404)

    if job_data.get('status') not in {'completed', 'failed'}:
        return redirect(url_for('users.bulk_user_import_progress', job_id=job_id))

    return render_template('users_bulk_import_result.html', job=job_data)


@bp.route('/users/import/bulk/errors/<job_id>', methods=['GET'])
@login_required
def bulk_user_import_download_errors(job_id):
    if not _ensure_bulk_import_permission():
        return redirect(url_for('users.list_users'))

    job_data = get_job(job_id)
    if not _is_job_owner_or_allowed(job_data):
        abort(404)

    report_path = job_data.get('errorReportPath')
    if not report_path or not os.path.exists(report_path):
        flash('Não há planilha de erros para este processamento.', 'warning')
        return redirect(url_for('users.bulk_user_import_result', job_id=job_id))

    return send_file(
        report_path,
        as_attachment=True,
        download_name=f'importacao_usuarios_erros_{job_id}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


# Configuration Management Routes

