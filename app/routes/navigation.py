from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.utils import enforce_feature_access

bp = Blueprint('navigation', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    denial = enforce_feature_access('dashboard_view', 'Acesso negado. Você não tem permissão para acessar o dashboard.')
    if denial:
        return denial

    return render_template('dashboard.html')


@bp.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

