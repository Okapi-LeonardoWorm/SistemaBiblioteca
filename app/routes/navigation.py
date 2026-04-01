from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

bp = Blueprint('navigation', __name__)

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.userType != 'admin':
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('navigation.menu'))

    return render_template('dashboard.html')


@bp.route('/menu')
@login_required
def menu():
    return render_template('menu.html')

