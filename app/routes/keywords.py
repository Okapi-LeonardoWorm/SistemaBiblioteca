from datetime import date

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import func

from app import db
from app.forms import KeyWordForm
from app.models import KeyWord, KeyWordBook
from app.utils import normalize_tag, parse_normalized_tags

bp = Blueprint('keywords', __name__)


def _active_keywords_query():
    return KeyWord.query.filter_by(deleted=False)


def _get_active_keyword_or_404(keyword_id):
    keyword = _active_keywords_query().filter_by(wordId=keyword_id).first()
    if not keyword:
        abort(404)
    return keyword

@bp.route('/palavras_chave')
@login_required
def palavras_chave():
    query = _active_keywords_query()
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
        keyword = _get_active_keyword_or_404(keyword_id)
        form = KeyWordForm(obj=keyword)
    else:
        form = KeyWordForm()
    return render_template('_keyword_form.html', form=form, keyword_id=keyword_id)


@bp.route('/api/palavras_chave/<int:id>/usage', methods=['GET'])
@login_required
def keyword_usage(id):
    keyword = db.session.get(KeyWord, id)
    if not keyword:
        abort(404)

    usage_count = db.session.query(
        func.count(func.distinct(KeyWordBook.bookId))
    ).filter(
        KeyWordBook.wordId == id
    ).scalar() or 0

    return jsonify({'success': True, 'usage_count': int(usage_count)})


@bp.route('/palavras_chave/new', methods=['POST'])
@login_required
def nova_palavra_chave():
    form = KeyWordForm()
    if form.validate_on_submit():
        parts = parse_normalized_tags(form.word.data)

        if not parts:
            return jsonify({'success': False, 'errors': {'word': ['Informe ao menos uma tag válida.']}})

        created = 0
        ignored = 0
        reactivated = 0
        existing_keywords = {
            kw.word: kw for kw in KeyWord.query.filter(KeyWord.word.in_(parts)).all()
        }

        for word in parts:
            existing = existing_keywords.get(word)
            if existing:
                if existing.deleted:
                    existing.deleted = False
                    existing.lastUpdate = date.today()
                    existing.updatedBy = current_user.userId
                    db.session.add(existing)
                    reactivated += 1
                else:
                    ignored += 1
                continue

            kw = KeyWord(
                word=word,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=current_user.userId,
                updatedBy=current_user.userId
            )
            db.session.add(kw)
            created += 1

        if created or reactivated:
            db.session.commit()

        msg = 'Tags processadas com sucesso.'
        if created and ignored and reactivated:
            msg = f'{created} nova(s) tag(s) criada(s); {reactivated} tag(s) reativada(s); {ignored} já existia(m) e foram ignoradas.'
        elif created and ignored:
            msg = f'{created} nova(s) tag(s) criada(s); {ignored} já existia(m) e foram ignoradas.'
        elif created and reactivated:
            msg = f'{created} nova(s) tag(s) criada(s); {reactivated} tag(s) reativada(s).'
        elif created and not ignored and not reactivated:
            msg = f'{created} nova(s) tag(s) criada(s).'
        elif reactivated and ignored:
            msg = f'{reactivated} tag(s) reativada(s); {ignored} já existia(m) e foram ignoradas.'
        elif reactivated and not ignored:
            msg = f'{reactivated} tag(s) reativada(s).'
        elif not created and not reactivated and ignored:
            msg = 'Todas as tags já existiam; nada foi criado.'

        flash(msg, 'success')
        return jsonify({'success': True, 'created': created, 'ignored': ignored, 'reactivated': reactivated})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/palavras_chave/edit/<int:keyword_id>', methods=['POST'])
@login_required
def editar_palavra_chave(keyword_id):
    keyword = _get_active_keyword_or_404(keyword_id)
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
    palavra_chave = db.session.get(KeyWord, id)
    if not palavra_chave:
        abort(404)

    was_already_deleted = bool(palavra_chave.deleted)
    if not palavra_chave.deleted:
        KeyWordBook.query.filter_by(wordId=palavra_chave.wordId).delete(synchronize_session=False)
        palavra_chave.deleted = True
        palavra_chave.lastUpdate = date.today()
        palavra_chave.updatedBy = current_user.userId
        db.session.add(palavra_chave)
        db.session.commit()

    is_async_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    message = 'Tag já estava marcada como excluída.' if was_already_deleted else 'Tag marcada como excluída com sucesso!'

    if is_async_request:
        return jsonify({'success': True, 'message': message})

    flash(message, 'success')
    return redirect(url_for('keywords.palavras_chave'))


# User Management Routes

