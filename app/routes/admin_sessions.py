from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user, login_required

from app import db
from app.models import UserSession

bp = Blueprint('admin_sessions', __name__)

@bp.route('/admin/sessions')
@login_required
def manage_sessions():
    if current_user.userType != 'admin':
        flash('Acesso negado. Apenas administradores podem ver as sessões.', 'danger')
        return redirect(url_for('auth.index'))
        
    sessions = UserSession.query.order_by(UserSession.last_activity.desc()).all()
    current_token = session.get('session_token')
    
    return render_template('admin_sessions.html', sessions=sessions, current_session_token=current_token)

@bp.route('/admin/sessions/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_session(session_id):
    if current_user.userType != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('auth.index'))
        
    user_session = UserSession.query.filter_by(session_id=session_id).first()
    if user_session:
        db.session.delete(user_session)
        db.session.commit()
        flash('Sessão encerrada com sucesso.', 'success')
    else:
        flash('Sessão não encontrada.', 'warning')
        
    return redirect(url_for('admin_sessions.manage_sessions'))

