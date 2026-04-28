from datetime import date, datetime
import io
import os
import threading

from flask import Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from flask_paginate import get_page_parameter
from sqlalchemy import or_

from app import db
from app.forms import BookForm
from app.models import Book, KeyWord
from app.services import (
    BOOK_BULK_REQUIRED_FIELDS_DISPLAY,
    BOOK_BULK_TEMPLATE_COLUMNS,
    build_book_bulk_template_rows,
    create_job,
    get_job,
    run_book_create_import_job,
)
from app.utils import (
    SUPPORTED_IMPORT_EXTENSIONS,
    build_template_bytes,
    can_access_feature,
    detect_extension,
    enforce_api_feature_access,
    enforce_feature_access,
    parse_normalized_tags,
)

bp = Blueprint('books', __name__)


def _parse_int(value):
    try:
        if value is None or value == '':
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_book_date_inputs(form):
    published_mode = form.publishedDateMode.data or 'year'
    acquisition_mode = form.acquisitionDateMode.data or 'year'

    if published_mode == 'date':
        published_date = form.publishedDate.data
        form.publicationYear.data = published_date.year if published_date else None
    else:
        form.publishedDate.data = None

    if acquisition_mode == 'date':
        acquisition_value = form.acquisitionDate.data
        if acquisition_value:
            form.acquisitionYear.data = acquisition_value.year
            if isinstance(acquisition_value, date) and not isinstance(acquisition_value, datetime):
                form.acquisitionDate.data = datetime.combine(acquisition_value, datetime.min.time())
        else:
            form.acquisitionYear.data = None
    else:
        form.acquisitionDate.data = None


def _ensure_book_bulk_import_permission():
    if not can_access_feature('books_bulk_import'):
        flash('Acesso negado. Somente admin e bibliotecário podem importar livros em massa.', 'warning')
        return False
    return True


def _is_book_job_owner_or_allowed(job_data: dict) -> bool:
    if not job_data:
        return False
    if current_user.userId == job_data.get('ownerUserId'):
        return True
    return can_access_feature('books_bulk_import')


def _active_books_query():
    return Book.query.filter_by(deleted=False)


def _get_active_book_or_404(book_id):
    book = _active_books_query().filter_by(bookId=book_id).first()
    if not book:
        abort(404)
    return book


def _get_book_or_404(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        abort(404)
    return book


def _build_sort_links(endpoint, base_params, sort_columns, current_sort_by, current_sort_dir):
    links = {}
    for key in sort_columns.keys():
        params = {k: v for k, v in base_params.items() if v is not None and v != ''}
        params['page'] = 1

        if current_sort_by != key:
            params['sort_by'] = key
            params['sort_dir'] = 'asc'
        elif current_sort_dir == 'asc':
            params['sort_by'] = key
            params['sort_dir'] = 'desc'
        else:
            params.pop('sort_by', None)
            params.pop('sort_dir', None)

        links[key] = url_for(endpoint, **params)
    return links

@bp.route('/livros')
@login_required
def livros():
    denial = enforce_feature_access('books_browse', 'Acesso negado para visualizar livros.')
    if denial:
        return denial

    include_deleted = request.args.get('include_deleted') == '1'
    if include_deleted and not can_access_feature('books_include_deleted'):
        include_deleted = False
    include_deleted_value = '1' if include_deleted else ''
    query = Book.query if include_deleted else _active_books_query()
    search_term = (request.args.get('search') or '').strip()
    sort_by = (request.args.get('sort_by') or '').strip()
    sort_dir = (request.args.get('sort_dir') or '').strip().lower()

    filters = {
        'book_author': (request.args.get('book_author') or '').strip(),
        'book_publisher': (request.args.get('book_publisher') or '').strip(),
        'book_published_start': (request.args.get('book_published_start') or '').strip(),
        'book_published_end': (request.args.get('book_published_end') or '').strip(),
        'book_acquired_start': (request.args.get('book_acquired_start') or '').strip(),
        'book_acquired_end': (request.args.get('book_acquired_end') or '').strip(),
        'book_amount_min': (request.args.get('book_amount_min') or '').strip(),
        'book_amount_max': (request.args.get('book_amount_max') or '').strip(),
        'book_description': (request.args.get('book_description') or '').strip(),
        'book_tags': (request.args.get('book_tags') or '').strip(),
    }

    needs_keywords_join = bool(filters['book_tags'])
    if needs_keywords_join:
        query = query.outerjoin(Book.keywords)

    if search_term:
        query = query.filter(
            or_(
                Book.bookName.ilike(f'%{search_term}%'),
                Book.authorName.ilike(f'%{search_term}%')
            )
        )

    if filters['book_author']:
        query = query.filter(Book.authorName.ilike(f"%{filters['book_author']}%"))
    if filters['book_publisher']:
        query = query.filter(Book.publisherName.ilike(f"%{filters['book_publisher']}%"))

    published_start = filters['book_published_start']
    published_end = filters['book_published_end']
    if published_start:
        query = query.filter(Book.publishedDate >= published_start)
    if published_end:
        query = query.filter(Book.publishedDate <= published_end)

    acquired_start = filters['book_acquired_start']
    acquired_end = filters['book_acquired_end']
    if acquired_start:
        query = query.filter(Book.acquisitionDate >= acquired_start)
    if acquired_end:
        query = query.filter(Book.acquisitionDate <= acquired_end)

    amount_min = _parse_int(filters['book_amount_min'])
    amount_max = _parse_int(filters['book_amount_max'])
    if amount_min is not None:
        query = query.filter(Book.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Book.amount <= amount_max)

    if filters['book_description']:
        query = query.filter(Book.description.ilike(f"%{filters['book_description']}%"))

    if filters['book_tags']:
        tags = parse_normalized_tags(filters['book_tags'])
        if tags:
            query = query.filter(or_(*[KeyWord.word.ilike(f'%{tag}%') for tag in tags]))

    if needs_keywords_join:
        query = query.distinct()

    sort_columns = {
        'title': Book.bookName,
        'author': Book.authorName,
        'publisher': Book.publisherName,
        'amount': Book.amount,
        'deleted': Book.deleted,
    }
    if sort_by not in sort_columns:
        sort_by = ''
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = ''

    if sort_by and sort_dir:
        sort_column = sort_columns[sort_by]
        if sort_dir == 'asc':
            query = query.order_by(sort_column.asc().nullslast())
        else:
            query = query.order_by(sort_column.desc().nullslast())
    else:
        query = query.order_by(Book.bookId.desc())

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = request.args.get('per_page', type=int, default=20)
    books_pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    base_params = {
        'search': search_term,
        'per_page': per_page,
        'include_deleted': include_deleted_value,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        **filters,
    }
    sort_links = _build_sort_links('books.livros', base_params, sort_columns, sort_by, sort_dir)
    
    return render_template(
        'livros.html',
        books=books_pagination,
        search_term=search_term,
        per_page=per_page,
        filters=filters,
        include_deleted=include_deleted,
        include_deleted_value=include_deleted_value,
        sort_by=sort_by,
        sort_dir=sort_dir,
        sort_links=sort_links,
    )


@bp.route('/livros/form', defaults={'book_id': None}, methods=['GET'])
@bp.route('/livros/form/<int:book_id>', methods=['GET'])
@login_required
def get_book_form(book_id):
    if book_id:
        denial = enforce_feature_access('books_browse', 'Acesso negado para visualizar o livro.')
    else:
        denial = enforce_feature_access('books_manage', 'Acesso negado para acessar o formulário de livros.')
    if denial:
        return denial

    book = None
    if book_id:
        book = _get_book_or_404(book_id)
        form = BookForm(obj=book)
        if book.publishedDate:
            form.publishedDateMode.data = 'date'
            if form.publicationYear.data is None:
                form.publicationYear.data = book.publishedDate.year
        else:
            form.publishedDateMode.data = 'year'

        if book.acquisitionDate:
            form.acquisitionDateMode.data = 'date'
            if form.acquisitionYear.data is None:
                form.acquisitionYear.data = book.acquisitionDate.year
        else:
            form.acquisitionDateMode.data = 'year'

        form.keyWords.data = '; '.join([kw.word for kw in book.keywords])
    else:
        form = BookForm()
    form_action = url_for('books.novo_livro') if not book_id else url_for('books.editar_livro', book_id=book_id)
    return render_template('_book_form.html', form=form, book_id=book_id, book=book, form_action=form_action)


@bp.route('/livros/new', methods=['POST'])
@login_required
def novo_livro():
    denial = enforce_feature_access('books_manage', 'Acesso negado para criar livros.')
    if denial:
        return denial

    form = BookForm()
    if form.validate_on_submit():
        _normalize_book_date_inputs(form)

        new_book = Book(
            bookName=(form.bookName.data or '').strip(),
            amount=form.amount.data,
            authorName=(form.authorName.data or '').strip() if form.authorName.data else None,
            publisherName=(form.publisherName.data or '').strip() if form.publisherName.data else None,
            publishedDate=form.publishedDate.data,
            publicationYear=form.publicationYear.data,
            acquisitionDate=form.acquisitionDate.data,
            acquisitionYear=form.acquisitionYear.data,
            description=(form.description.data or '').strip() if form.description.data else None,
            creationDate=date.today(),
            lastUpdate=date.today(),
            createdBy=current_user.userId,
            updatedBy=current_user.userId,
        )
        db.session.add(new_book)
        db.session.commit()
        
        keywords_list = parse_normalized_tags(form.keyWords.data)
        
        for keyword_str in keywords_list:
            keyword_obj = KeyWord.query.filter_by(word=keyword_str, deleted=False).first()
            if not keyword_obj:
                keyword_obj = KeyWord.query.filter_by(word=keyword_str, deleted=True).first()
                if keyword_obj:
                    keyword_obj.deleted = False
                    keyword_obj.lastUpdate = date.today()
                    keyword_obj.updatedBy = current_user.userId
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
    denial = enforce_feature_access('books_manage', 'Acesso negado para editar livros.')
    if denial:
        return denial

    book = _get_book_or_404(book_id)
    form = BookForm(request.form)
    
    if form.validate():
        _normalize_book_date_inputs(form)
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
        
        new_keywords = set(parse_normalized_tags(form.keyWords.data))
        
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
                keyword_obj = KeyWord.query.filter_by(word=keyword_str, deleted=False).first()
                if not keyword_obj:
                    keyword_obj = KeyWord.query.filter_by(word=keyword_str, deleted=True).first()
                    if keyword_obj:
                        keyword_obj.deleted = False
                        keyword_obj.lastUpdate = date.today()
                        keyword_obj.updatedBy = current_user.userId
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
    denial = enforce_feature_access('books_delete', 'Acesso negado para excluir livros.')
    if denial:
        return denial

    livro = _get_book_or_404(id)

    was_already_deleted = bool(livro.deleted)
    if not livro.deleted:
        livro.deleted = True
        livro.lastUpdate = date.today()
        livro.updatedBy = current_user.userId
        db.session.add(livro)
        db.session.commit()

    is_async_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    message = 'Livro já estava marcado como excluído.' if was_already_deleted else 'Livro marcado como excluído com sucesso!'

    if is_async_request:
        return jsonify({'success': True, 'message': message})

    flash(message, 'success')
    return redirect(url_for('books.livros'))


@bp.route('/reativar_livro/<int:id>', methods=['POST'])
@login_required
def reativar_livro(id):
    denial = enforce_feature_access('books_delete', 'Acesso negado para reativar livros.')
    if denial:
        return denial

    livro = _get_book_or_404(id)

    was_already_active = not bool(livro.deleted)
    if livro.deleted:
        livro.deleted = False
        livro.lastUpdate = date.today()
        livro.updatedBy = current_user.userId
        db.session.add(livro)
        db.session.commit()

    is_async_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    message = 'Livro já estava ativo.' if was_already_active else 'Livro reativado com sucesso!'

    if is_async_request:
        return jsonify({'success': True, 'message': message})

    flash(message, 'success')
    return redirect(url_for('books.livros'))


@bp.route('/livros/import/bulk', methods=['GET'])
@login_required
def bulk_book_import_entry():
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    return redirect(url_for('books.bulk_book_import_upload'))


@bp.route('/livros/import/bulk/upload', methods=['GET', 'POST'])
@login_required
def bulk_book_import_upload():
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    if request.method == 'POST':
        upload_file = request.files.get('importFile')
        if not upload_file or not upload_file.filename:
            flash('Selecione um arquivo CSV ou XLSX para continuar.', 'danger')
            return render_template('books_bulk_import_upload.html', required_fields=BOOK_BULK_REQUIRED_FIELDS_DISPLAY)

        extension = detect_extension(upload_file.filename)
        if extension not in SUPPORTED_IMPORT_EXTENSIONS:
            flash('Formato de arquivo inválido. Use CSV ou XLSX.', 'danger')
            return render_template('books_bulk_import_upload.html', required_fields=BOOK_BULK_REQUIRED_FIELDS_DISPLAY)

        jobs_root = os.path.join(current_app.instance_path, 'bulk_import_jobs')
        uploads_root = os.path.join(jobs_root, 'uploads')
        errors_root = os.path.join(jobs_root, 'errors')
        os.makedirs(uploads_root, exist_ok=True)
        os.makedirs(errors_root, exist_ok=True)

        job_id = create_job(
            owner_user_id=current_user.userId,
            kind='book_bulk_create',
            metadata={
                'originalFilename': upload_file.filename,
            },
        )

        source_path = os.path.join(uploads_root, f'{job_id}.{extension}')
        error_report_path = os.path.join(errors_root, f'{job_id}_erros.xlsx')
        upload_file.save(source_path)

        app_obj = current_app._get_current_object()
        worker = threading.Thread(
            target=run_book_create_import_job,
            args=(
                app_obj,
                job_id,
                source_path,
                extension,
                current_user.userId,
                error_report_path,
            ),
            daemon=True,
        )
        worker.start()

        return redirect(url_for('books.bulk_book_import_progress', job_id=job_id))

    return render_template('books_bulk_import_upload.html', required_fields=BOOK_BULK_REQUIRED_FIELDS_DISPLAY)


@bp.route('/livros/import/bulk/template', methods=['GET'])
@login_required
def bulk_book_import_download_template():
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    output_format = (request.args.get('format') or 'xlsx').strip().lower()
    if output_format not in SUPPORTED_IMPORT_EXTENSIONS:
        flash('Formato inválido. Use CSV ou XLSX.', 'warning')
        return redirect(url_for('books.bulk_book_import_upload'))

    headers = list(BOOK_BULK_TEMPLATE_COLUMNS)
    sample_rows = build_book_bulk_template_rows()
    content = build_template_bytes(output_format, headers, sample_rows)

    mimetype = 'text/csv; charset=utf-8' if output_format == 'csv' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(
        io.BytesIO(content),
        as_attachment=True,
        download_name=f'modelo_importacao_livros.{output_format}',
        mimetype=mimetype,
    )


@bp.route('/livros/import/bulk/progress/<job_id>', methods=['GET'])
@login_required
def bulk_book_import_progress(job_id):
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    job_data = get_job(job_id)
    if not _is_book_job_owner_or_allowed(job_data):
        abort(404)

    return render_template('books_bulk_import_progress.html', job_id=job_id)


@bp.route('/livros/import/bulk/status/<job_id>', methods=['GET'])
@login_required
def bulk_book_import_status(job_id):
    denial = enforce_api_feature_access('books_bulk_import')
    if denial:
        return denial

    job_data = get_job(job_id)
    if not _is_book_job_owner_or_allowed(job_data):
        return jsonify({'success': False, 'error': 'Job não encontrado.'}), 404

    return jsonify({'success': True, 'job': job_data})


@bp.route('/livros/import/bulk/result/<job_id>', methods=['GET'])
@login_required
def bulk_book_import_result(job_id):
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    job_data = get_job(job_id)
    if not _is_book_job_owner_or_allowed(job_data):
        abort(404)

    if job_data.get('status') not in {'completed', 'failed'}:
        return redirect(url_for('books.bulk_book_import_progress', job_id=job_id))

    return render_template('books_bulk_import_result.html', job=job_data)


@bp.route('/livros/import/bulk/errors/<job_id>', methods=['GET'])
@login_required
def bulk_book_import_download_errors(job_id):
    denial = enforce_feature_access('books_bulk_import', 'Acesso negado para importar livros em massa.')
    if denial:
        return denial

    job_data = get_job(job_id)
    if not _is_book_job_owner_or_allowed(job_data):
        abort(404)

    report_path = job_data.get('errorReportPath')
    if not report_path or not os.path.exists(report_path):
        flash('Não há planilha de erros para este processamento.', 'warning')
        return redirect(url_for('books.bulk_book_import_result', job_id=job_id))

    return send_file(
        report_path,
        as_attachment=True,
        download_name=f'importacao_livros_erros_{job_id}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

