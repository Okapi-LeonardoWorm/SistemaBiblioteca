from datetime import datetime, timedelta, timezone

from flask import current_app, flash, redirect, session, url_for
from flask_login import current_user, logout_user

from app import db
from app.models import Configuration, UserSession


def check_session_timeout(login_endpoint: str = 'auth.login'):
    if not current_user.is_authenticated:
        return None

    session.permanent = False
    now = datetime.now(timezone.utc)
    current_session_token = session.get('session_token')

    if current_session_token:
        user_session = UserSession.query.filter_by(session_id=current_session_token).first()

        if not user_session:
            logout_user()
            session.clear()
            flash('Sua sessão foi encerrada remotamente.', 'warning')
            return redirect(url_for(login_endpoint))

        config_inactivity = Configuration.query.filter_by(key='SESSION_INACTIVITY_MINUTES').first()
        inactivity_minutes = int(config_inactivity.value) if (config_inactivity and config_inactivity.value.isdigit()) else 60

        last_activity = user_session.last_activity
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)

        if now - last_activity > timedelta(minutes=inactivity_minutes):
            db.session.delete(user_session)
            db.session.commit()
            logout_user()
            session.clear()
            flash('Sua sessão expirou por inatividade.', 'warning')
            return redirect(url_for(login_endpoint))

        user_session.last_activity = now
        db.session.commit()

    start_time_str = session.get('session_start')
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str)
            config_db = Configuration.query.filter_by(key='SESSION_LIFETIME_HOURS').first()
            if config_db and config_db.value.isdigit():
                limit_hours = int(config_db.value)
            else:
                limit_config = current_app.config.get('PERMANENT_SESSION_LIFETIME')
                limit_hours = limit_config.total_seconds() / 3600 if limit_config else 12

            limit = timedelta(hours=limit_hours)
            if now - start_time > limit:
                if current_session_token:
                    UserSession.query.filter_by(session_id=current_session_token).delete()
                    db.session.commit()

                logout_user()
                session.clear()
                flash('Sua sessão expirou (limite de tempo total). Por favor, faça login novamente.', 'warning')
                return redirect(url_for(login_endpoint))
        except (ValueError, TypeError):
            logout_user()
            session.clear()
            return redirect(url_for(login_endpoint))

    return None
