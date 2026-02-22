from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter

from app import db
from app.forms import KeyWordForm
from app.models import KeyWord
from app.utils import normalize_tag

bp = Blueprint('keywords', __name__)

@bp.route('/palavras_chave')
@login_required
def palavras_chave():
    query = KeyWord.query
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(KeyWord.word.ilike(f'%{search_term}%'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    keywords_pagination = query.order_by(KeyWord.word.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('palavras_chave.html', keywords=keywords_pagination, search_term=search_term, per_page=per_page)


@bp.route('/palavras_chave/form', defaults={'keyword_id': None}, methods=['GET'])
@bp.route('/palavras_chave/form/<int:keyword_id>', methods=['GET'])
@login_required
def get_keyword_form(keyword_id):
    if keyword_id:
        keyword = KeyWord.query.get_or_404(keyword_id)
        form = KeyWordForm(obj=keyword)
    else:
        form = KeyWordForm()
    return render_template('_keyword_form.html', form=form, keyword_id=keyword_id)


@bp.route('/palavras_chave/new', methods=['POST'])
@login_required
def nova_palavra_chave():
    form = KeyWordForm()
    if form.validate_on_submit():
        raw = form.word.data or ''
        # split por vírgula ou ponto e vírgula
        parts = []
        seen = set()
        for token in raw.replace(';', ',').split(','):
            normalized = normalize_tag(token)
            if normalized and normalized not in seen:
                parts.append(normalized)
                seen.add(normalized)

        if not parts:
            return jsonify({'success': False, 'errors': {'word': ['Informe ao menos uma tag válida.']}})

        # buscar existentes
        existing = {kw.word for kw in KeyWord.query.filter(KeyWord.word.in_(parts)).all()}
        to_create = [p for p in parts if p not in existing]

        created = 0
        for w in to_create:
            kw = KeyWord(
                word=w,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=current_user.userId,
                updatedBy=current_user.userId
            )
            db.session.add(kw)
            created += 1
        if created:
            db.session.commit()
        msg = 'Tags processadas com sucesso.'
        if created and existing:
            msg = f'{created} nova(s) tag(s) criada(s); {len(existing)} já existia(m) e foram ignoradas.'
        elif created and not existing:
            msg = f'{created} nova(s) tag(s) criada(s).'
        elif not created and existing:
            msg = 'Todas as tags já existiam; nada foi criado.'
        flash(msg, 'success')
        return jsonify({'success': True, 'created': created, 'ignored': len(existing)})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/palavras_chave/edit/<int:keyword_id>', methods=['POST'])
@login_required
def editar_palavra_chave(keyword_id):
    keyword = KeyWord.query.get_or_404(keyword_id)
    form = KeyWordForm(request.form)
    if form.validate():
        normalized = normalize_tag(form.word.data or '')
        if not normalized:
            return jsonify({'success': False, 'errors': {'word': ['Informe uma tag válida.']}})
        # verificar duplicidade com outras tags
        existing = KeyWord.query.filter_by(word=normalized).first()
        if existing and existing.word != keyword.word:
            return jsonify({'success': False, 'errors': {'word': ['Esta tag já existe.']}})

        keyword.word = normalized
        keyword.lastUpdate = date.today()
        keyword.updatedBy = current_user.userId
        db.session.commit()
        flash('Tag atualizada com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/excluir_palavra_chave/<int:id>', methods=['POST'])
@login_required
def excluir_palavra_chave(id):
    palavra_chave = KeyWord.query.get_or_404(id)
    db.session.delete(palavra_chave)
    db.session.commit()
    flash('Palavra-chave excluída com sucesso!', 'success')
    return redirect(url_for('keywords.palavras_chave'))


# User Management Routes

