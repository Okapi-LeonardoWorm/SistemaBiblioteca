from app.models import ConfigSpec


def parse_allowed_values(raw: str):
    return [item.strip() for item in (raw or '').split(',') if item.strip()]


def normalize_boolean_string(raw_value: str):
    normalized = (raw_value or '').strip().lower()
    if normalized in ('1', 'true', 'sim', 'yes'):
        return '1'
    if normalized in ('0', 'false', 'nao', 'não', 'no'):
        return '0'
    return None


def validate_config_value(raw_value: str, spec: ConfigSpec):
    value = (raw_value or '').strip()
    if spec.required and not value:
        return False, None, 'Este valor é obrigatório.'
    if not value:
        return True, '', None

    if spec.valueType == 'boolean':
        bool_value = normalize_boolean_string(value)
        if bool_value is None:
            return False, None, 'Valor inválido. Para booleano, use 0 ou 1.'
        return True, bool_value, None

    if spec.valueType == 'integer':
        try:
            int_value = int(value)
        except (TypeError, ValueError):
            return False, None, 'Valor inválido. Informe um número inteiro.'

        if spec.minValue is not None and int_value < spec.minValue:
            return False, None, f'Valor deve ser maior ou igual a {spec.minValue}.'
        if spec.maxValue is not None and int_value > spec.maxValue:
            return False, None, f'Valor deve ser menor ou igual a {spec.maxValue}.'
        return True, str(int_value), None

    if spec.valueType == 'enum':
        allowed = parse_allowed_values(spec.allowedValues)
        if not allowed:
            return False, None, 'A configuração enum não possui opções válidas definidas.'
        if value not in allowed:
            return False, None, f'Valor inválido. Opções permitidas: {", ".join(allowed)}.'
        return True, value, None

    return True, value, None


def build_or_update_spec_from_form(form, existing_spec: ConfigSpec | None = None):
    spec = existing_spec or ConfigSpec()
    spec.key = form.key.data
    spec.valueType = form.valueType.data
    spec.allowedValues = (form.allowedValues.data or '').strip() or None
    spec.minValue = form.minValue.data if form.valueType.data == 'integer' else None
    spec.maxValue = form.maxValue.data if form.valueType.data == 'integer' else None
    spec.required = bool(form.required.data)
    spec.defaultValue = (form.defaultValue.data or '').strip() or None
    spec.description = (form.specDescription.data or '').strip() or None
    return spec
