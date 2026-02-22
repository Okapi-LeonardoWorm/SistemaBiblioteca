from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app import db
from app.forms import BookForm
from app.models import Book, KeyWord
from app.utils import normalize_tag, split_string_into_list

bp = Blueprint('books', __name__)

@bp.route('/livros')
@login_required
def livros():
    query = Book.query
    search_term = request.args.get('search', '')
    if search_term:
        query = query.filter(
            or_(
                Book.bookName.ilike(f'%{search_term}%'),
                Book.authorName.ilike(f'%{search_term}%')
            )
        )

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    books_pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('livros.html', books=books_pagination, search_term=search_term, per_page=per_page)


@bp.route('/livros/form', defaults={'book_id': None}, methods=['GET'])
@bp.route('/livros/form/<int:book_id>', methods=['GET'])
@login_required
def get_book_form(book_id):
    if book_id:
        book = Book.query.get_or_404(book_id)
        form = BookForm(obj=book)
        form.keyWords.data = '; '.join([kw.word for kw in book.keywords])
    else:
        form = BookForm()
    return render_template('_book_form.html', form=form, book_id=book_id)


@bp.route('/livros/new', methods=['POST'])
@login_required
def novo_livro():
    form = BookForm()
    if form.validate_on_submit():
        new_book = Book(
            bookName=(form.bookName.data or '').strip(),
            amount=form.amount.data,
            authorName=(form.authorName.data or '').strip() if form.authorName.data else None,
            publisherName=(form.publisherName.data or '').strip() if form.publisherName.data else None,
            publishedDate=form.publishedDate.data,
            acquisitionDate=form.acquisitionDate.data,
            description=(form.description.data or '').strip() if form.description.data else None,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        db.session.add(new_book)
        db.session.commit()
        
        # Processar keywords com normalize_tag
        raw_keywords = split_string_into_list(form.keyWords.data)
        # normalize_tag retorna string vazia se inválido
        keywords_list = [normalized for k in raw_keywords if (normalized := normalize_tag(k))]
        
        for keyword_str in keywords_list:
            keyword_obj = KeyWord.query.filter_by(word=keyword_str).first()
            if not keyword_obj:
                keyword_obj = KeyWord(word=keyword_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                db.session.add(keyword_obj)
            new_book.keywords.append(keyword_obj)
        db.session.commit()

        flash('Livro cadastrado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


@bp.route('/livros/edit/<int:book_id>', methods=['POST'])
@login_required
def editar_livro(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(request.form)
    
    if form.validate():
        has_changes = False
        
        # 1. Verificar campos simples
        # Obs: campos como bookName, authorName etc
        for field in form:
            if field.name in ['csrf_token', 'keyWords']: continue
            if not hasattr(book, field.name): continue
            
            old_val = getattr(book, field.name)
            new_val = field.data
            
            # Normalizar None e String Vazia
            if isinstance(old_val, str) and new_val is None: new_val = ''
            if old_val is None and isinstance(new_val, str): old_val = ''
            
            if old_val != new_val:
                has_changes = True
                break
        
        # 2. Verificar keywords
        current_keywords = {kw.word for kw in book.keywords}
        
        raw_keywords = split_string_into_list(form.keyWords.data)
        # normalize_tag retorna string vazia se inválido
        new_keywords = {normalized for k in raw_keywords if (normalized := normalize_tag(k))}
        
        if current_keywords != new_keywords:
            has_changes = True
            
        if not has_changes:
            # Se nada mudou, retorna sucesso sem tocar no banco
            return jsonify({'success': True, 'message': 'Nenhuma alteração detectada.'})

        form.populate_obj(book)
        
        new_keywords_str = new_keywords
        old_keywords_str = current_keywords
        
        for keyword_obj in list(book.keywords):
            if keyword_obj.word not in new_keywords_str:
                book.keywords.remove(keyword_obj)
        
        for keyword_str in new_keywords_str:
            if keyword_str not in old_keywords_str:
                keyword_obj = KeyWord.query.filter_by(word=keyword_str).first()
                if not keyword_obj:
                    keyword_obj = KeyWord(word=keyword_str, creationDate=date.today(), lastUpdate=date.today(), createdBy=current_user.userId, updatedBy=current_user.userId)
                    db.session.add(keyword_obj)
                book.keywords.append(keyword_obj)

        book.lastUpdate = date.today()
        book.updatedBy = current_user.userId
        db.session.commit()
        flash('Livro atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    return jsonify({'success': False, 'errors': form.errors})


# Loan Management Routes


@bp.route('/excluir_livro/<int:id>', methods=['POST'])
@login_required
def excluir_livro(id):
    livro = Book.query.get_or_404(id)
    db.session.delete(livro)
    db.session.commit()
    flash('Livro excluído com sucesso!', 'success')
    return redirect(url_for('books.livros'))

