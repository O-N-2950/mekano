from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def tenant_required(fn):
    """Decorator that extracts garage_id from JWT and sets it on flask.g."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        g.garage_id = claims.get("garage_id")
        g.user_id = claims.get("user_id")
        g.user_role = claims.get("role")
        if not g.garage_id:
            return {"error": "Tenant non identifie"}, 403
        return fn(*args, **kwargs)

    return wrapper
