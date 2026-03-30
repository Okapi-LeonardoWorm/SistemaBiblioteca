from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app import db
from app.forms import ConfigForm
from app.models import ConfigSpec, Configuration
from app.utils import build_or_update_spec_from_form, is_admin_user, validate_config_value

bp = Blueprint('configs', __name__)

@bp.route('/configuracoes')
@login_required
def configuracoes():
    if not is_admin_user():
        flash('Acesso negado. Você precisa ser um administrador.', 'warning')
        return redirect(url_for('navigation.menu'))

    query = Configuration.query
    search_term = (request.args.get('search') or '').strip()
    if search_term:
        query = query.filter(
            or_(
                Configuration.key.ilike(f'%{search_term}%'),
                Configuration.description.ilike(f'%{search_term}%')
            )
        )

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    configs = query.order_by(Configuration.key.asc(), Configuration.configId.asc()).paginate(page=page, per_page=per_page, error_out=False)

    keys = [cfg.key for cfg in configs.items if cfg.key]
    specs_by_key = {}
    if keys:
        specs = ConfigSpec.query.filter(ConfigSpec.key.in_(keys)).all()
        specs_by_key = {spec.key: spec for spec in specs}

    return render_template('configuracoes.html', configs=configs, search_term=search_term, per_page=per_page, specs_by_key=specs_by_key)


@bp.route('/configuracoes/form', defaults={'config_id': None}, methods=['GET'])
@bp.route('/configuracoes/form/<int:config_id>', methods=['GET'])
@login_required
def get_config_form(config_id):
    if not is_admin_user():
        return '<p class="text-danger">Acesso negado.</p>', 403

    if config_id:
        config = db.session.get(Configuration, config_id)
        if not config:
            abort(404)
        form = ConfigForm(obj=config)
        spec = ConfigSpec.query.filter_by(key=config.key).first()
        if spec:
            form.valueType.data = spec.valueType
            form.allowedValues.data = spec.allowedValues
            form.minValue.data = spec.minValue
            form.maxValue.data = spec.maxValue
            form.required.data = spec.required
            form.defaultValue.data = spec.defaultValue
            form.specDescription.data = spec.description
    else:
        config = None
        form = ConfigForm()
        form.valueType.data = 'string'

    return render_template('_config_form.html', form=form, config=config, config_id=config_id)


@bp.route('/configuracoes/new', methods=['POST'])
@login_required
def nova_configuracao():
    if not is_admin_user():
        return jsonify({'success': False, 'errors': {'auth': ['Acesso negado.']}}), 403

    form = ConfigForm()
    if not form.validate_on_submit():
        return jsonify({'success': False, 'errors': form.errors})

    existing = Configuration.query.filter_by(key=form.key.data).first()
    if existing:
        return jsonify({'success': False, 'errors': {'key': ['Esta chave já existe. Edite o registro existente.']}})

    spec = build_or_update_spec_from_form(form)
    ok, normalized_value, error_msg = validate_config_value(form.value.data, spec)
    if not ok:
        return jsonify({'success': False, 'errors': {'value': [error_msg]}})

    spec.createdBy = current_user.userId
    spec.updatedBy = current_user.userId
    spec.creationDate = datetime.now()
    spec.lastUpdate = datetime.now()

    new_config = Configuration(
        key=form.key.data,
        value=normalized_value,
        description=(form.description.data or '').strip() or None,
        creationDate=datetime.now(),
        lastUpdate=datetime.now(),
        createdBy=current_user.userId,
        updatedBy=current_user.userId,
    )
    db.session.add(spec)
    db.session.add(new_config)
    db.session.commit()
    flash('Configuração criada com sucesso!', 'success')
    return jsonify({'success': True})


@bp.route('/configuracoes/edit/<int:config_id>', methods=['POST'])
@login_required
def editar_configuracao(config_id):
    if not is_admin_user():
        return jsonify({'success': False, 'errors': {'auth': ['Acesso negado.']}}), 403

    config = db.session.get(Configuration, config_id)
    if not config:
        abort(404)
    form = ConfigForm(request.form)
    if not form.validate():
        return jsonify({'success': False, 'errors': form.errors})

    if form.key.data != config.key:
        return jsonify({'success': False, 'errors': {'key': ['A chave não pode ser alterada na edição.']}})

    spec = ConfigSpec.query.filter_by(key=config.key).first()
    spec = build_or_update_spec_from_form(form, spec)
    ok, normalized_value, error_msg = validate_config_value(form.value.data, spec)
    if not ok:
        return jsonify({'success': False, 'errors': {'value': [error_msg]}})

    if not spec.configSpecId:
        spec.createdBy = current_user.userId
        spec.creationDate = datetime.now()
        db.session.add(spec)

    spec.updatedBy = current_user.userId
    spec.lastUpdate = datetime.now()

    config.value = normalized_value
    config.description = (form.description.data or '').strip() or None
    config.lastUpdate = datetime.now()
    config.updatedBy = current_user.userId
    db.session.commit()
    flash('Configuração atualizada com sucesso!', 'success')
    return jsonify({'success': True})

