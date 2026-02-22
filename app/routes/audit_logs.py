from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload

from app.models import AuditLog, User
from app.utils import is_admin_user

bp = Blueprint('audit_logs', __name__)

@bp.route('/audit_logs')
@login_required
def audit_logs():
    if not is_admin_user():
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('auth.index'))

    # Pagination
    try:
        page = request.args.get('page', 1, type=int)
    except ValueError:
        page = 1
    per_page = 20

    # Filter params
    action_filter = request.args.get('action', '').strip()
    target_type_filter = request.args.get('target_type', '').strip()
    user_id_filter = request.args.get('user_id', '').strip()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    query = AuditLog.query.options(joinedload(AuditLog.user))

    if action_filter:
        query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))
    
    if target_type_filter:
        query = query.filter(AuditLog.target_type.ilike(f"%{target_type_filter}%"))

    if user_id_filter:
        try:
            uid = int(user_id_filter)
            query = query.filter(AuditLog.user_id == uid)
        except ValueError:
             # Se for string (nome), tenta buscar pelo ID
             user_obj = User.query.filter(User.identificationCode.ilike(f"%{user_id_filter}%")).first()
             if user_obj:
                 query = query.filter(AuditLog.user_id == user_obj.userId)
             else:
                 query = query.filter(AuditLog.user_id == -1) # força vazio

    if start_date_str:
        try:
             start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
             query = query.filter(AuditLog.timestamp >= start_dt)
        except ValueError:
             pass

    if end_date_str:
        try:
             end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
             # Ajusta para final do dia
             end_dt = end_dt.replace(hour=23, minute=59, second=59)
             query = query.filter(AuditLog.timestamp <= end_dt)
        except ValueError:
             pass

    query = query.order_by(AuditLog.timestamp.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items

    return render_template('audit_logs.html', logs=logs, pagination=pagination)

