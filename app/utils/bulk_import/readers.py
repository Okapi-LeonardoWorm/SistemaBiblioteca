import csv
import importlib
import posixpath
import zipfile
from xml.etree import ElementTree as ET
from typing import Dict, Iterator, List, Tuple


SUPPORTED_IMPORT_EXTENSIONS = {'csv', 'xlsx'}


def detect_extension(filename: str) -> str:
    if '.' not in (filename or ''):
        return ''
    return filename.rsplit('.', 1)[1].lower().strip()


def _sanitize_header(value) -> str:
    text = '' if value is None else str(value)
    return text.strip()


def _sanitize_value(value):
    if value is None:
        return ''
    return value


def _try_openpyxl_load_workbook():
    try:
        openpyxl = importlib.import_module('openpyxl')
        return getattr(openpyxl, 'load_workbook')
    except Exception:
        return None


def _column_index_from_cell_ref(cell_ref: str) -> int:
    letters = ''.join(ch for ch in (cell_ref or '') if ch.isalpha()).upper()
    result = 0
    for ch in letters:
        result = (result * 26) + (ord(ch) - 64)
    return result


def _read_xlsx_shared_strings(zip_file: zipfile.ZipFile) -> List[str]:
    shared_strings = []
    if 'xl/sharedStrings.xml' not in zip_file.namelist():
        return shared_strings

    with zip_file.open('xl/sharedStrings.xml') as shared_stream:
        tree = ET.parse(shared_stream)
        root = tree.getroot()
        # Each <si> can contain multiple <t> nodes.
        for si in root.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            texts = []
            for t_node in si.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                texts.append(t_node.text or '')
            shared_strings.append(''.join(texts))
    return shared_strings


def _first_sheet_xml_path(zip_file: zipfile.ZipFile) -> str:
    workbook_path = 'xl/workbook.xml'
    workbook_rels_path = 'xl/_rels/workbook.xml.rels'
    if workbook_path not in zip_file.namelist() or workbook_rels_path not in zip_file.namelist():
        return 'xl/worksheets/sheet1.xml'

    with zip_file.open(workbook_path) as workbook_stream:
        workbook_tree = ET.parse(workbook_stream)
        workbook_root = workbook_tree.getroot()

    sheet_node = workbook_root.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')
    if sheet_node is None:
        return 'xl/worksheets/sheet1.xml'

    rel_id = sheet_node.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
    if not rel_id:
        return 'xl/worksheets/sheet1.xml'

    with zip_file.open(workbook_rels_path) as rels_stream:
        rels_tree = ET.parse(rels_stream)
        rels_root = rels_tree.getroot()

    for rel_node in rels_root.findall('{http://schemas.openxmlformats.org/package/2006/relationships}Relationship'):
        if rel_node.attrib.get('Id') == rel_id:
            target = rel_node.attrib.get('Target', 'worksheets/sheet1.xml')
            normalized_target = (target or '').replace('\\', '/').lstrip('/')
            if normalized_target.startswith('xl/'):
                return posixpath.normpath(normalized_target)
            return posixpath.normpath(posixpath.join('xl', normalized_target))

    return 'xl/worksheets/sheet1.xml'


def _parse_xlsx_cell_value(cell_node: ET.Element, shared_strings: List[str]):
    value_node = cell_node.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
    inline_node = cell_node.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is')
    cell_type = cell_node.attrib.get('t')

    if cell_type == 'inlineStr' and inline_node is not None:
        texts = []
        for t_node in inline_node.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
            texts.append(t_node.text or '')
        return ''.join(texts)

    if value_node is None or value_node.text is None:
        return ''

    raw_value = value_node.text
    if cell_type == 's':
        try:
            idx = int(raw_value)
            return shared_strings[idx] if 0 <= idx < len(shared_strings) else ''
        except (TypeError, ValueError):
            return ''

    if cell_type == 'b':
        return '1' if raw_value == '1' else '0'

    return raw_value


def _iter_xlsx_rows_with_stdlib(file_path: str) -> Iterator[List[object]]:
    with zipfile.ZipFile(file_path, mode='r') as zip_file:
        shared_strings = _read_xlsx_shared_strings(zip_file)
        sheet_path = _first_sheet_xml_path(zip_file)
        if sheet_path not in zip_file.namelist():
            return

        with zip_file.open(sheet_path) as sheet_stream:
            context = ET.iterparse(sheet_stream, events=('end',))
            for _, elem in context:
                if not elem.tag.endswith('row'):
                    continue

                cells = []
                max_column = 0
                for cell in elem:
                    if not cell.tag.endswith('c'):
                        continue
                    cell_ref = cell.attrib.get('r', '')
                    column_idx = _column_index_from_cell_ref(cell_ref)
                    if column_idx <= 0:
                        continue
                    max_column = max(max_column, column_idx)
                    cells.append((column_idx, _parse_xlsx_cell_value(cell, shared_strings)))

                if max_column <= 0:
                    yield []
                else:
                    row_values = [''] * max_column
                    for column_idx, value in cells:
                        row_values[column_idx - 1] = value
                    yield row_values

                elem.clear()


def read_headers(file_path: str, extension: str) -> List[str]:
    ext = (extension or '').lower().strip()
    if ext == 'csv':
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csv_file:
            reader = csv.reader(csv_file)
            first_row = next(reader, None)
            if first_row is None:
                return []
            return [_sanitize_header(value) for value in first_row]

    if ext == 'xlsx':
        load_workbook = _try_openpyxl_load_workbook()
        if load_workbook:
            workbook = load_workbook(filename=file_path, read_only=True, data_only=True)
            try:
                sheet = workbook.active
                first_row = next(sheet.iter_rows(min_row=1, max_row=1, values_only=True), None)
                if first_row is None:
                    return []
                return [_sanitize_header(value) for value in first_row]
            finally:
                workbook.close()

        first_row = next(_iter_xlsx_rows_with_stdlib(file_path), None)
        if first_row is None:
            return []
        return [_sanitize_header(value) for value in first_row]

    raise ValueError(f'Extensão não suportada: {extension}')


def iter_rows(file_path: str, extension: str) -> Iterator[Tuple[int, Dict[str, object]]]:
    ext = (extension or '').lower().strip()
    if ext == 'csv':
        with open(file_path, mode='r', encoding='utf-8-sig', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            if not reader.fieldnames:
                return
            headers = [_sanitize_header(name) for name in reader.fieldnames]
            for index, row in enumerate(reader, start=2):
                normalized_row = {}
                for header in headers:
                    normalized_row[header] = _sanitize_value((row or {}).get(header))
                yield index, normalized_row
        return

    if ext == 'xlsx':
        load_workbook = _try_openpyxl_load_workbook()
        if load_workbook:
            workbook = load_workbook(filename=file_path, read_only=True, data_only=True)
            try:
                sheet = workbook.active
                rows_iter = sheet.iter_rows(values_only=True)
                header_row = next(rows_iter, None)
                if header_row is None:
                    return
                headers = [_sanitize_header(value) for value in header_row]

                for index, row_values in enumerate(rows_iter, start=2):
                    normalized_row = {}
                    for col_index, header in enumerate(headers):
                        cell_value = row_values[col_index] if row_values and col_index < len(row_values) else ''
                        normalized_row[header] = _sanitize_value(cell_value)
                    yield index, normalized_row
            finally:
                workbook.close()
            return

        rows_iter = _iter_xlsx_rows_with_stdlib(file_path)
        header_row = next(rows_iter, None)
        if header_row is None:
            return
        headers = [_sanitize_header(value) for value in header_row]

        for index, row_values in enumerate(rows_iter, start=2):
            normalized_row = {}
            for col_index, header in enumerate(headers):
                cell_value = row_values[col_index] if row_values and col_index < len(row_values) else ''
                normalized_row[header] = _sanitize_value(cell_value)
            yield index, normalized_row
        return

    raise ValueError(f'Extensão não suportada: {extension}')


def count_data_rows(file_path: str, extension: str) -> int:
    total = 0
    for _, _ in iter_rows(file_path, extension):
        total += 1
    return total
