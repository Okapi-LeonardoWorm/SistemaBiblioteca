from datetime import date, datetime, timezone
from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import AnonymousUserMixin, current_user, login_required, login_user, logout_user

from app import bcrypt, db
from app.audit import log_manual_event
from app.forms import LoginForm, RegisterForm
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
    if current_user.userType == 'admin':
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
    form = LoginForm()
    if form.validate_on_submit():
        usernameStr = form.username.data.strip().lower()
        # Agora o login utiliza o identificationCode no lugar de username
        user = User.query.filter_by(identificationCode=usernameStr).first()
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
            session['username'] = usernameStr
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

                log_manual_event('LOGIN', 'User', user.userId, changes={'username': usernameStr})
            except Exception:
                pass
            if user.userType == 'admin':
                return redirect(url_for('navigation.dashboard'))
            return redirect(url_for('auth.index'))
        else:
            flash('Usuário ou senha inválidos', 'danger')
            
    return render_template('login.html', form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    # Dynamically set choices for userType
    if isinstance(current_user, AnonymousUserMixin) or not current_user.is_authenticated:
        # Not logged in
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante')]
    elif current_user.userType == 'admin':
        # Logged in as admin
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante'), ('staff', 'Funcionário'), ('admin', 'Administrador')]
    else:
        # Logged in as non-admin (e.g., staff)
        form.userType.choices = [('student', 'Estudante'), ('visitor', 'Visitante'), ('staff', 'Funcionário')]

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # Determine createdBy and updatedBy
        creator_id = 1  # Default to system admin or a predefined ID
        if current_user.is_authenticated:
            creator_id = current_user.userId

        new_user = User(
            identificationCode=form.username.data.strip().lower(),
            userCompleteName=form.username.data.strip(),
            password=hashed_password,
            userType=form.userType.data,
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
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=creator_id,
            updatedBy=creator_id
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Usuário registrado com sucesso!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', form=form)


# Book Management Routes

