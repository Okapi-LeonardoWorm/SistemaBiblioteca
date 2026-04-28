from datetime import datetime, timezone
from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app import bcrypt, db
from app.audit import log_manual_event
from app.forms import LoginForm
from app.models import User, UserSession
from app.utils import check_session_timeout

bp = Blueprint('auth', __name__)


@bp.before_app_request
def check_session_timeout_hook():
    return check_session_timeout(login_endpoint='auth.login')

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    if current_user.userType in ['admin', 'bibliotecario']:
        return redirect(url_for('navigation.dashboard'))
    return redirect(url_for('navigation.menu'))


@bp.route('/logout')
@login_required
def logout():
    try:
        log_manual_event('LOGOUT', 'User', current_user.userId)
    except Exception:
        pass
        
    # Remove sessão do servidor se existir
    session_token = session.get('session_token')
    if session_token:
        try:
            db.session.query(UserSession).filter_by(session_id=session_token).delete()
            db.session.commit()
        except:
            pass

    session.clear()
    logout_user()
    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    form = LoginForm()
    if form.validate_on_submit():
        login_identifier = form.username.data.strip().lower()
        # Login por código de identificação (incluindo emails) sem diferenciação de maiúsculas/minúsculas.
        user = User.query.filter(
            func.lower(User.identificationCode) == login_identifier,
            User.deleted.is_(False),
        ).first()
        valid_password = False
        if user:
            try:
                valid_password = bcrypt.check_password_hash(user.password, form.password.data)
            except ValueError:
                # Se a senha no banco não estiver hasheada (ex.: em testes), faz comparação direta - REMOVER APÓS MIGRAÇÃO PARA PRODUÇÃO!
                valid_password = (user.password == form.password.data)
        if user and valid_password:
            # Generate Session Token
            token_str = str(uuid4())
            
            session['logged_in'] = True
            session['username'] = login_identifier
            session['userId'] = user.userId
            session['userType'] = user.userType
            session['session_start'] = datetime.now(timezone.utc).isoformat()
            session['session_token'] = token_str

            login_user(user)

            # Grava no banco
            try:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr) # Use a separate variable
                user_agent = request.headers.get('User-Agent')
                new_session = UserSession(
                    user_id=user.userId,
                    session_id=token_str,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(timezone.utc),
                    last_activity=datetime.now(timezone.utc)
                )
                db.session.add(new_session)
                db.session.commit()

                log_manual_event('LOGIN', 'User', user.userId, changes={'identifier': login_identifier})
            except Exception:
                pass
            return redirect(url_for('auth.index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
            
    return render_template('login.html', form=form)
