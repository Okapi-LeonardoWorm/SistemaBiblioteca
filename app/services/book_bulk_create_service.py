import os
import re
import unicodedata
from datetime import date, datetime

from werkzeug.datastructures import MultiDict

from app import db
from app.forms import BookForm
from app.models import Book, KeyWord
from app.services.bulk_jobs import add_job_message, update_job
from app.utils import parse_normalized_tags
from app.utils.bulk_import import ErrorReportWriter, checkpoint_progress, count_data_rows, iter_rows, read_headers


FIELD_ALIASES = {
    'bookName': ['NomeLivro', 'bookName', 'titulo', 'nome_livro', 'nome'],
    'amount': ['Quantidade', 'amount', 'qtd', 'quantidade_exemplares'],
    'authorName': ['Autor', 'authorName', 'nome_autor'],
    'publisherName': ['Editora', 'publisherName', 'nome_editora'],
    'publicationYear': ['AnoPublicacao', 'publicationYear', 'ano_publicacao'],
    'publishedDate': ['DataPublicacao', 'publishedDate', 'data_publicacao'],
    'acquisitionYear': ['AnoAquisicao', 'acquisitionYear', 'ano_aquisicao'],
    'acquisitionDate': ['DataAquisicao', 'acquisitionDate', 'data_aquisicao'],
    'description': ['Descricao', 'description', 'descricao', 'resumo'],
    'keyWords': ['Tags', 'keyWords', 'palavras_chave', 'keywords'],
}

TEMPLATE_FIELD_ORDER = [
    'bookName',
    'amount',
    'authorName',
    'publisherName',
    'publicationYear',
    'publishedDate',
    'acquisitionYear',
    'acquisitionDate',
    'description',
    'keyWords',
]

FIELD_LABELS = {
    'bookName': 'NomeLivro',
    'amount': 'Quantidade',
    'authorName': 'Autor',
    'publisherName': 'Editora',
    'publicationYear': 'AnoPublicacao',
    'publishedDate': 'DataPublicacao',
    'acquisitionYear': 'AnoAquisicao',
    'acquisitionDate': 'DataAquisicao',
    'description': 'Descricao',
    'keyWords': 'Tags',
}

REPORT_META_LABELS = {
    'linha': 'Linha',
    'database': 'BancoDeDados',
}

BOOK_BULK_REQUIRED_FIELDS = ['bookName', 'amount']
BOOK_BULK_REQUIRED_FIELDS_DISPLAY = [FIELD_LABELS[field] for field in BOOK_BULK_REQUIRED_FIELDS]
BOOK_BULK_TEMPLATE_COLUMNS = [FIELD_LABELS[field] for field in TEMPLATE_FIELD_ORDER]


def canonicalize_header(value: str) -> str:
    text = '' if value is None else str(value)
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')


def normalize_optional(value):
    if value is None:
        return ''
    text = str(value)
    if not text.strip():
        return ''
    return text.strip()


def format_date_for_form(value):
    if value is None:
        return ''

    if isinstance(value, datetime):
        return value.date().strftime('%Y-%m-%d')

    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')

    text = normalize_optional(value)
    if not text:
        return ''

    for date_fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            parsed = datetime.strptime(text, date_fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue

    return text


def _resolve_column_value(raw_row: dict, target_field: str):
    normalized = {}
    for key, value in (raw_row or {}).items():
        normalized[canonicalize_header(key)] = value

    for alias in FIELD_ALIASES.get(target_field, [target_field]):
        alias_key = canonicalize_header(alias)
        if alias_key in normalized:
            return normalized[alias_key]

    return None


def get_book_bulk_field_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name)


def build_book_bulk_template_rows() -> list[dict]:
    sample_row = {FIELD_LABELS[field]: '' for field in TEMPLATE_FIELD_ORDER}
    sample_row[FIELD_LABELS['bookName']] = 'Dom Casmurro'
    sample_row[FIELD_LABELS['amount']] = '3'
    sample_row[FIELD_LABELS['authorName']] = 'Machado de Assis'
    sample_row[FIELD_LABELS['publisherName']] = 'Editora Exemplo'
    sample_row[FIELD_LABELS['publicationYear']] = '1899'
    sample_row[FIELD_LABELS['acquisitionDate']] = '15/02/2026'
    sample_row[FIELD_LABELS['description']] = 'Exemplo de descricao do livro.'
    sample_row[FIELD_LABELS['keyWords']] = 'CLASSICO; ROMANCE'
    return [sample_row]


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


def _build_form_data(raw_row: dict):
    published_date = format_date_for_form(_resolve_column_value(raw_row, 'publishedDate'))
    acquisition_date = format_date_for_form(_resolve_column_value(raw_row, 'acquisitionDate'))

    publication_year = normalize_optional(_resolve_column_value(raw_row, 'publicationYear'))
    acquisition_year = normalize_optional(_resolve_column_value(raw_row, 'acquisitionYear'))

    if published_date and not publication_year:
        publication_year = published_date[:4]
    if acquisition_date and not acquisition_year:
        acquisition_year = acquisition_date[:4]

    data = {
        'bookName': normalize_optional(_resolve_column_value(raw_row, 'bookName')),
        'amount': normalize_optional(_resolve_column_value(raw_row, 'amount')),
        'authorName': normalize_optional(_resolve_column_value(raw_row, 'authorName')),
        'publisherName': normalize_optional(_resolve_column_value(raw_row, 'publisherName')),
        'publishedDateMode': 'date' if published_date else 'year',
        'publicationYear': publication_year,
        'publishedDate': published_date,
        'acquisitionDateMode': 'date' if acquisition_date else 'year',
        'acquisitionYear': acquisition_year,
        'acquisitionDate': acquisition_date,
        'description': normalize_optional(_resolve_column_value(raw_row, 'description')),
        'keyWords': normalize_optional(_resolve_column_value(raw_row, 'keyWords')),
    }
    return data


def _validate_required_fields(form_data: dict):
    errors = {}
    for field_name in BOOK_BULK_REQUIRED_FIELDS:
        if not normalize_optional(form_data.get(field_name, '')):
            errors.setdefault(field_name, []).append('Campo obrigatorio nao informado na planilha.')
    return errors


def _translate_single_error_message_ptbr(message: str) -> str:
    text = str(message or '').strip()
    if not text:
        return text

    exact_messages = {
        'This field is required.': 'Campo obrigatorio nao informado na planilha.',
        'Not a valid date value.': 'Data invalida.',
        'Not a valid date.': 'Data invalida.',
        'Not a valid integer value.': 'Numero inteiro invalido.',
        'Number must be at least 1.': 'Numero deve ser no minimo 1.',
        'Invalid input.': 'Entrada invalida.',
    }
    if text in exact_messages:
        return exact_messages[text]

    between_match = re.match(r'^Field must be between (\d+) and (\d+) characters long\.$', text)
    if between_match:
        min_chars, max_chars = between_match.groups()
        return f'Campo deve ter entre {min_chars} e {max_chars} caracteres.'

    at_least_match = re.match(r'^Field must be at least (\d+) characters long\.$', text)
    if at_least_match:
        return f'Campo deve ter no minimo {at_least_match.group(1)} caracteres.'

    at_most_match = re.match(r'^Field cannot be longer than (\d+) characters\.$', text)
    if at_most_match:
        return f'Campo deve ter no maximo {at_most_match.group(1)} caracteres.'

    number_between_match = re.match(r'^Number must be between ([\-\d]+) and ([\-\d]+)\.$', text)
    if number_between_match:
        min_value, max_value = number_between_match.groups()
        return f'Numero deve estar entre {min_value} e {max_value}.'

    duplicate_match = re.search(r'duplicate key value violates unique constraint', text, flags=re.IGNORECASE)
    if duplicate_match:
        return 'Valor duplicado para um campo unico no banco de dados.'

    if text.startswith('Erro ao persistir livro:'):
        details = text.split(':', 1)[1].strip() if ':' in text else ''
        details_ptbr = _translate_single_error_message_ptbr(details)
        return f'Erro ao persistir livro: {details_ptbr}' if details_ptbr else 'Erro ao persistir livro.'

    return text


def _translate_error_messages_ptbr(messages):
    if not isinstance(messages, list):
        return _translate_single_error_message_ptbr(messages)

    translated_messages = [_translate_single_error_message_ptbr(msg) for msg in messages]

    # If type conversion fails, range validation adds noise for the same field.
    has_integer_type_error = any(msg == 'Numero inteiro invalido.' for msg in translated_messages)
    if has_integer_type_error:
        translated_messages = [
            msg for msg in translated_messages
            if msg != 'Numero deve estar entre 1000 e 9999.'
        ]

    deduped = []
    for msg in translated_messages:
        if msg not in deduped:
            deduped.append(msg)
    return deduped


def translate_error_keys_for_report(errors_by_field: dict) -> dict:
    translated = {}
    for field_name, messages in (errors_by_field or {}).items():
        label = FIELD_LABELS.get(field_name) or REPORT_META_LABELS.get(field_name) or field_name
        translated[label] = _translate_error_messages_ptbr(messages)
    return translated


def _create_book_from_form(form: BookForm, imported_by: int):
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
        createdBy=imported_by,
        updatedBy=imported_by,
    )

    db.session.add(new_book)

    keywords_list = parse_normalized_tags(form.keyWords.data)
    for keyword_str in keywords_list:
        keyword_obj = KeyWord.query.filter_by(word=keyword_str).first()
        if not keyword_obj:
            keyword_obj = KeyWord(
                word=keyword_str,
                creationDate=date.today(),
                lastUpdate=date.today(),
                createdBy=imported_by,
                updatedBy=imported_by,
            )
            db.session.add(keyword_obj)
        new_book.keywords.append(keyword_obj)

    db.session.commit()


def run_book_create_import_job(app, job_id: str, file_path: str, extension: str, imported_by: int, error_report_path: str):
    with app.app_context():
        report_writer = None
        try:
            update_job(job_id, status='running', progress=0)
            headers = read_headers(file_path, extension)
            total_rows = count_data_rows(file_path, extension)

            update_job(job_id, summary={'totalRows': total_rows})
            report_writer = ErrorReportWriter(error_report_path, headers)

            processed_rows = 0
            success_rows = 0
            error_rows = 0
            current_progress = 0

            for source_line, raw_row in iter_rows(file_path, extension):
                processed_rows += 1
                row_errors = {}

                form_data = _build_form_data(raw_row)
                required_errors = _validate_required_fields(form_data)
                for field_name, messages in required_errors.items():
                    row_errors.setdefault(field_name, []).extend(messages)

                form = BookForm(formdata=MultiDict(form_data), meta={'csrf': False})
                if not row_errors and not form.validate():
                    for field_name, messages in form.errors.items():
                        row_errors.setdefault(field_name, []).extend(messages)

                if row_errors:
                    row_errors.setdefault('linha', []).append(f'Linha original: {source_line}')
                    report_writer.append(raw_row, translate_error_keys_for_report(row_errors))
                    error_rows += 1
                else:
                    try:
                        _create_book_from_form(form, imported_by)
                        success_rows += 1
                    except Exception as exc:
                        db.session.rollback()
                        error_rows += 1
                        report_writer.append(raw_row, translate_error_keys_for_report({
                            'database': [f'Erro ao persistir livro: {exc}'],
                            'linha': [f'Linha original: {source_line}'],
                        }))

                current_progress = checkpoint_progress(processed_rows, total_rows, current_progress)
                update_job(
                    job_id,
                    progress=current_progress,
                    summary={
                        'processedRows': processed_rows,
                        'successRows': success_rows,
                        'errorRows': error_rows,
                    },
                )

            has_error_rows = report_writer.close()
            if not has_error_rows and os.path.exists(error_report_path):
                os.remove(error_report_path)
                error_report_path = None

            update_job(
                job_id,
                status='completed',
                progress=100,
                errorReportPath=error_report_path,
                summary={
                    'processedRows': processed_rows,
                    'successRows': success_rows,
                    'errorRows': error_rows,
                },
            )
        except Exception as exc:
            db.session.rollback()
            if report_writer is not None:
                try:
                    report_writer.close()
                except Exception:
                    pass
            add_job_message(job_id, 'Falha durante a importacao.')
            update_job(job_id, status='failed', progress=100)
