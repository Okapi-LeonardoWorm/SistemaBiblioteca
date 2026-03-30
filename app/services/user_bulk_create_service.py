import os
import re
import unicodedata
from datetime import date, datetime

from werkzeug.datastructures import MultiDict

from app import bcrypt, db
from app.forms import UserForm
from app.models import Configuration, User
from app.services.bulk_jobs import add_job_message, update_job
from app.utils.bulk_import import ErrorReportWriter, checkpoint_progress, count_data_rows, iter_rows, read_headers


FIELD_ALIASES = {
    'identificationCode': ['Login', 'identificationCode', 'codigo_identificacao', 'codigo', 'username', 'matricula'],
    'password': ['Senha', 'password', 'senha'],
    'userCompleteName': ['NomeCompleto', 'userCompleteName', 'nome_completo', 'nome'],
    'birthDate': ['DataNascimento', 'birthDate', 'data_nascimento', 'nascimento'],
    'userPhone': ['Celular', 'userPhone', 'telefone', 'celular'],
    'cpf': ['cpf'],
    'rg': ['rg'],
    'gradeNumber': ['Ano', 'gradeNumber', 'numero_serie', 'serie'],
    'className': ['Turma', 'className', 'turma'],
    'guardianName1': ['1TutorNome', 'guardianName1', 'nome_responsavel_1', 'responsavel_1'],
    'guardianPhone1': ['1TutorCelular', 'guardianPhone1', 'telefone_responsavel_1', 'celular_responsavel_1'],
    'guardianName2': ['2TutorNome', 'guardianName2', 'nome_responsavel_2', 'responsavel_2'],
    'guardianPhone2': ['2TutorCelular', 'guardianPhone2', 'telefone_responsavel_2', 'celular_responsavel_2'],
    'notes': ['Observações', 'notes', 'observacoes', 'observacao', 'obs'],
    'pcd': ['PCD', 'pcd'],
}

CONFIG_REQUIRED_FIELDS_BY_TYPE = {
    'aluno': 'BULK_IMPORT_USER_REQUIRED_COLUMNS_ALUNO',
    'colaborador': 'BULK_IMPORT_USER_REQUIRED_COLUMNS_COLABORADOR',
    'bibliotecario': 'BULK_IMPORT_USER_REQUIRED_COLUMNS_BIBLIOTECARIO',
    'admin': 'BULK_IMPORT_USER_REQUIRED_COLUMNS_ADMIN',
}

TEMPLATE_FIELD_ORDER = [
    'identificationCode',
    'password',
    'userCompleteName',
    'birthDate',
    'userPhone',
    'cpf',
    'rg',
    'gradeNumber',
    'className',
    'guardianName1',
    'guardianPhone1',
    'guardianName2',
    'guardianPhone2',
    'notes',
    'pcd',
]

FIELD_LABELS = {
    'identificationCode': 'Login',
    'password': 'Senha',
    'userCompleteName': 'NomeCompleto',
    'birthDate': 'DataNascimento',
    'userPhone': 'Celular',
    'cpf': 'CPF',
    'rg': 'RG',
    'gradeNumber': 'Ano',
    'className': 'Turma',
    'guardianName1': '1TutorNome',
    'guardianPhone1': '1TutorCelular',
    'guardianName2': '2TutorNome',
    'guardianPhone2': '2TutorCelular',
    'notes': 'Observações',
    'pcd': 'PCD',
}

REPORT_META_LABELS = {
    'linha': 'Linha',
    'database': 'BancoDeDados',
}

USER_BULK_TEMPLATE_COLUMNS = [FIELD_LABELS[field] for field in TEMPLATE_FIELD_ORDER]


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


def parse_pcd(value):
    text = normalize_optional(value).lower()
    if text in ('', 'nao', 'não', 'n', 'no', 'false', '0'):
        return True, False, None
    if text in ('sim', 's', 'yes', 'true', '1'):
        return True, True, None
    return False, False, "Valor invalido para PCD. Use 'sim' ou 'nao'."


def format_birth_date_for_form(value):
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

    # Preserve original to let existing form validators report invalid format.
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


def get_required_fields_for_user_type(user_type: str):
    key = CONFIG_REQUIRED_FIELDS_BY_TYPE.get(user_type)
    if not key:
        return ['identificationCode', 'password', 'userCompleteName', 'birthDate']

    config = Configuration.query.filter_by(key=key).first()
    if not config or not config.value:
        return ['identificationCode', 'password', 'userCompleteName', 'birthDate']

    parsed = [item.strip() for item in str(config.value).split(',') if item.strip()]
    return parsed or ['identificationCode', 'password', 'userCompleteName', 'birthDate']


def get_bulk_field_label(field_name: str) -> str:
    return FIELD_LABELS.get(field_name, field_name)


def _translate_single_error_message_ptbr(message: str) -> str:
    text = str(message or '').strip()
    if not text:
        return text

    exact_messages = {
        'This field is required.': 'Este campo é obrigatório.',
        'Not a valid date value.': 'Data inválida.',
        'Not a valid date.': 'Data inválida.',
        'Not a valid integer value.': 'Número inteiro inválido.',
        'Invalid input.': 'Entrada inválida.',
    }
    if text in exact_messages:
        return exact_messages[text]

    between_match = re.match(r'^Field must be between (\d+) and (\d+) characters long\.$', text)
    if between_match:
        min_chars, max_chars = between_match.groups()
        return f'Campo deve ter entre {min_chars} e {max_chars} caracteres.'

    at_least_match = re.match(r'^Field must be at least (\d+) characters long\.$', text)
    if at_least_match:
        return f'Campo deve ter no mínimo {at_least_match.group(1)} caracteres.'

    at_most_match = re.match(r'^Field cannot be longer than (\d+) characters\.$', text)
    if at_most_match:
        return f'Campo deve ter no máximo {at_most_match.group(1)} caracteres.'

    duplicate_match = re.search(r'duplicate key value violates unique constraint', text, flags=re.IGNORECASE)
    if duplicate_match:
        return 'Valor duplicado para um campo único no banco de dados.'

    if text.startswith('Erro ao persistir usuario:'):
        details = text.split(':', 1)[1].strip() if ':' in text else ''
        details_ptbr = _translate_single_error_message_ptbr(details)
        return f'Erro ao persistir usuário: {details_ptbr}' if details_ptbr else 'Erro ao persistir usuário.'

    return text


def _translate_error_messages_ptbr(messages):
    if isinstance(messages, list):
        return [_translate_single_error_message_ptbr(msg) for msg in messages]
    return _translate_single_error_message_ptbr(messages)


def translate_error_keys_for_report(errors_by_field: dict) -> dict:
    translated = {}
    for field_name, messages in (errors_by_field or {}).items():
        label = FIELD_LABELS.get(field_name) or REPORT_META_LABELS.get(field_name) or field_name
        translated[label] = _translate_error_messages_ptbr(messages)
    return translated


def build_user_bulk_template_rows(selected_user_type: str) -> list[dict]:
    required_fields = set(get_required_fields_for_user_type(selected_user_type))
    sample_row = {FIELD_LABELS[field]: '' for field in TEMPLATE_FIELD_ORDER}

    sample_row[FIELD_LABELS['identificationCode']] = 'ALUNO001' if selected_user_type == 'aluno' else 'USER001'
    sample_row[FIELD_LABELS['password']] = 'senha123'
    sample_row[FIELD_LABELS['userCompleteName']] = 'Nome Completo'
    sample_row[FIELD_LABELS['birthDate']] = '11/03/2005'
    sample_row[FIELD_LABELS['userPhone']] = '11999998888'
    sample_row[FIELD_LABELS['pcd']] = 'nao'

    if selected_user_type == 'aluno':
        sample_row[FIELD_LABELS['gradeNumber']] = '7'
        sample_row[FIELD_LABELS['className']] = 'A'
        sample_row[FIELD_LABELS['guardianName1']] = 'Responsavel 1'
        sample_row[FIELD_LABELS['guardianPhone1']] = '11911112222'

    # Keep required fields visible with a simple marker for quick orientation.
    for field_name in required_fields:
        display_name = FIELD_LABELS.get(field_name, field_name)
        if not sample_row.get(display_name):
            sample_row[display_name] = 'OBRIGATORIO'

    return [sample_row]


def _build_form_data(raw_row: dict, selected_user_type: str):
    pcd_ok, pcd_value, pcd_error = parse_pcd(_resolve_column_value(raw_row, 'pcd'))

    data = {
        'userType': selected_user_type,
        'identificationCode': normalize_optional(_resolve_column_value(raw_row, 'identificationCode')),
        'password': normalize_optional(_resolve_column_value(raw_row, 'password')),
        'userCompleteName': normalize_optional(_resolve_column_value(raw_row, 'userCompleteName')),
        'birthDate': format_birth_date_for_form(_resolve_column_value(raw_row, 'birthDate')),
        'userPhone': normalize_optional(_resolve_column_value(raw_row, 'userPhone')),
        'cpf': normalize_optional(_resolve_column_value(raw_row, 'cpf')),
        'rg': normalize_optional(_resolve_column_value(raw_row, 'rg')),
        'gradeNumber': normalize_optional(_resolve_column_value(raw_row, 'gradeNumber')),
        'className': normalize_optional(_resolve_column_value(raw_row, 'className')),
        'guardianName1': normalize_optional(_resolve_column_value(raw_row, 'guardianName1')),
        'guardianPhone1': normalize_optional(_resolve_column_value(raw_row, 'guardianPhone1')),
        'guardianName2': normalize_optional(_resolve_column_value(raw_row, 'guardianName2')),
        'guardianPhone2': normalize_optional(_resolve_column_value(raw_row, 'guardianPhone2')),
        'notes': normalize_optional(_resolve_column_value(raw_row, 'notes')),
        'pcd': 'y' if pcd_value else '',
    }

    return data, pcd_ok, pcd_error


def _validate_required_fields(form_data: dict, required_fields: list[str]):
    errors = {}
    for field_name in required_fields:
        if not normalize_optional(form_data.get(field_name, '')):
            errors.setdefault(field_name, []).append('Campo obrigatorio nao informado na planilha.')
    return errors


def _create_user_from_form(form: UserForm, imported_by: int):
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    new_user = User(
        identificationCode=form.identificationCode.data.strip(),
        userCompleteName=form.userCompleteName.data.strip(),
        password=hashed_password,
        userType=form.userType.data,
        creationDate=date.today(),
        lastUpdate=date.today(),
        createdBy=imported_by,
        updatedBy=imported_by,
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
        pcd=bool(form.pcd.data),
    )

    db.session.add(new_user)
    db.session.commit()


def run_user_create_import_job(app, job_id: str, file_path: str, extension: str, selected_user_type: str, imported_by: int, error_report_path: str):
    with app.app_context():
        report_writer = None
        try:
            update_job(job_id, status='running', progress=0)
            headers = read_headers(file_path, extension)
            total_rows = count_data_rows(file_path, extension)
            required_fields = get_required_fields_for_user_type(selected_user_type)

            update_job(job_id, summary={'totalRows': total_rows})
            report_writer = ErrorReportWriter(error_report_path, headers)

            processed_rows = 0
            success_rows = 0
            error_rows = 0
            current_progress = 0

            for source_line, raw_row in iter_rows(file_path, extension):
                processed_rows += 1
                row_errors = {}

                form_data, pcd_ok, pcd_error = _build_form_data(raw_row, selected_user_type)
                if not pcd_ok:
                    row_errors.setdefault('pcd', []).append(pcd_error)

                required_errors = _validate_required_fields(form_data, required_fields)
                for field_name, messages in required_errors.items():
                    row_errors.setdefault(field_name, []).extend(messages)

                form = UserForm(formdata=MultiDict(form_data), meta={'csrf': False}, mode='create')
                if not row_errors and not form.validate():
                    for field_name, messages in form.errors.items():
                        row_errors.setdefault(field_name, []).extend(messages)

                if row_errors:
                    row_errors.setdefault('linha', []).append(f'Linha original: {source_line}')
                    report_writer.append(raw_row, translate_error_keys_for_report(row_errors))
                    error_rows += 1
                else:
                    try:
                        _create_user_from_form(form, imported_by)
                        success_rows += 1
                    except Exception as exc:
                        db.session.rollback()
                        error_rows += 1
                        report_writer.append(raw_row, translate_error_keys_for_report({
                            'database': [f'Erro ao persistir usuario: {exc}'],
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
