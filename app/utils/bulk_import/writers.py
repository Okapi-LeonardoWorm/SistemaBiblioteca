from .template_builder import build_xlsx_template_bytes


class ErrorReportWriter:
    def __init__(self, output_path: str, headers):
        self.output_path = output_path
        self.headers = list(headers or [])
        self._rows = []
        self._has_error_rows = False

    def append(self, row_data: dict, errors_by_column: dict):
        ordered_values = [row_data.get(header, '') for header in self.headers]
        formatted_errors = []
        for column_name, messages in (errors_by_column or {}).items():
            if not messages:
                continue
            if isinstance(messages, list):
                joined = '; '.join(str(msg) for msg in messages)
            else:
                joined = str(messages)
            formatted_errors.append(f'{column_name}: {joined}')

        error_entry = dict(zip(self.headers, ordered_values))
        error_entry['erros_validacao'] = ' | '.join(formatted_errors)
        self._rows.append(error_entry)
        self._has_error_rows = True

    def close(self):
        xlsx_content = build_xlsx_template_bytes(self.headers + ['erros_validacao'], self._rows)
        with open(self.output_path, mode='wb') as output_file:
            output_file.write(xlsx_content)
        return self._has_error_rows
