import re
from datetime import date, datetime

# Format plaque CH : 2 lettres (canton) + espace + 1-6 chiffres
# Ex: VD 345678, BE 12345, ZH 1234
PLAQUE_CH_REGEX = re.compile(
    r"^(AG|AI|AR|BE|BL|BS|FR|GE|GL|GR|JU|LU|NE|NW|OW|SG|SH|SO|SZ|TG|TI|UR|VD|VS|ZG|ZH)\s\d{1,6}$"
)


def validate_plaque_ch(plaque):
    if not plaque:
        return True
    return bool(PLAQUE_CH_REGEX.match(plaque.strip().upper()))


def validate_required(data, fields):
    errors = {}
    for field in fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            errors[field] = "Ce champ est requis"
    return errors


def validate_email(email):
    if not email:
        return True
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def parse_datetime(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None
