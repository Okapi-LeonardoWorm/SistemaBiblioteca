import csv
import io
from xml.sax.saxutils import escape
import zipfile


def build_csv_template_bytes(headers: list[str], rows: list[dict]) -> bytes:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key, '') for key in headers})
    return output.getvalue().encode('utf-8-sig')


def _column_letter(column_index: int) -> str:
    result = ''
    current = column_index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _build_sheet_xml(headers: list[str], rows: list[dict]) -> str:
    all_rows = [headers] + [[row.get(key, '') for key in headers] for row in rows]
    row_parts = []

    for row_idx, values in enumerate(all_rows, start=1):
        cell_parts = []
        for col_idx, value in enumerate(values, start=1):
            cell_ref = f'{_column_letter(col_idx)}{row_idx}'
            text = '' if value is None else str(value)
            cell_parts.append(
                f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>'
            )
        row_parts.append(f'<row r="{row_idx}">{"".join(cell_parts)}</row>')

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_parts)}</sheetData>'
        '</worksheet>'
    )


def build_xlsx_template_bytes(headers: list[str], rows: list[dict]) -> bytes:
    output = io.BytesIO()
    sheet_xml = _build_sheet_xml(headers, rows)

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '</Types>'
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" '
        'Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" '
        'Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" '
        'Target="docProps/app.xml"/>'
        '</Relationships>'
    )

    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Modelo" sheetId="1" r:id="rId1"/></sheets>'
        '</workbook>'
    )

    workbook_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )

    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>Modelo de Importacao</dc:title>'
        '<dc:creator>Sistema Biblioteca</dc:creator>'
        '</cp:coreProperties>'
    )

    app_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        '<Application>Sistema Biblioteca</Application>'
        '</Properties>'
    )

    with zipfile.ZipFile(output, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('[Content_Types].xml', content_types_xml)
        zip_file.writestr('_rels/.rels', rels_xml)
        zip_file.writestr('xl/workbook.xml', workbook_xml)
        zip_file.writestr('xl/_rels/workbook.xml.rels', workbook_rels_xml)
        zip_file.writestr('xl/worksheets/sheet1.xml', sheet_xml)
        zip_file.writestr('docProps/core.xml', core_xml)
        zip_file.writestr('docProps/app.xml', app_xml)

    return output.getvalue()


def build_template_bytes(output_format: str, headers: list[str], rows: list[dict]) -> bytes:
    fmt = (output_format or '').strip().lower()
    if fmt == 'csv':
        return build_csv_template_bytes(headers, rows)
    if fmt == 'xlsx':
        return build_xlsx_template_bytes(headers, rows)
    raise ValueError('Formato de template não suportado. Use csv ou xlsx.')
