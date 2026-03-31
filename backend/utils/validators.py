"""
utils/validators.py
--------------------
Backend validation helpers for Flask request data.

Usage:
    from utils.validators import validate, rules

    errors = validate(data, {
        "email":    [rules.required, rules.email],
        "password": [rules.required, rules.min_length(6)],
        "cgpa":     [rules.cgpa],
    })
    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 422
"""

import re
from datetime import datetime


# ── Rule factories ─────────────────────────────────────────────────────────────

class rules:
    @staticmethod
    def required(val, label="This field"):
        if val is None or str(val).strip() == "":
            return f"{label} is required."

    @staticmethod
    def email(val, label="Email"):
        if val and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", str(val).strip()):
            return f"{label} must be a valid email address."

    @staticmethod
    def min_length(n):
        def _check(val, label="This field"):
            if val and len(str(val).strip()) < n:
                return f"{label} must be at least {n} characters."
        return _check

    @staticmethod
    def max_length(n):
        def _check(val, label="This field"):
            if val and len(str(val).strip()) > n:
                return f"{label} must not exceed {n} characters."
        return _check

    @staticmethod
    def numeric(val, label="This field"):
        if val is not None and val != "":
            try:
                float(val)
            except (ValueError, TypeError):
                return f"{label} must be a number."

    @staticmethod
    def cgpa(val, label="CGPA"):
        if val is not None and val != "":
            try:
                f = float(val)
                if not (0 <= f <= 10):
                    return f"{label} must be between 0 and 10."
            except (ValueError, TypeError):
                return f"{label} must be a valid number."

    @staticmethod
    def salary(val, label="Salary"):
        if val is not None and val != "":
            try:
                f = float(val)
                if f < 0:
                    return f"{label} cannot be negative."
            except (ValueError, TypeError):
                return f"{label} must be a valid number."

    @staticmethod
    def future_date(val, label="Date"):
        if val:
            try:
                dt = datetime.fromisoformat(str(val))
                if dt < datetime.utcnow():
                    return f"{label} must be in the future."
            except (ValueError, TypeError):
                return f"{label} must be a valid date."

    @staticmethod
    def url(val, label="URL"):
        if val and not re.match(r"^https?://\S+\.\S+", str(val).strip()):
            return f"{label} must start with http:// or https://"

    @staticmethod
    def phone(val, label="Phone"):
        if val and not re.match(r"^[+\d\s\-()\[\]]{7,20}$", str(val).strip()):
            return f"{label} must be a valid phone number."

    @staticmethod
    def choice(*options):
        def _check(val, label="Value"):
            if val and val not in options:
                return f"{label} must be one of: {', '.join(str(o) for o in options)}"
        return _check


# ── Runner ─────────────────────────────────────────────────────────────────────

def validate(data: dict, rules_map: dict) -> dict:
    """
    Run validation rules against a data dict.

    Parameters
    ----------
    data      : dict  — request payload (e.g. request.get_json())
    rules_map : dict  — { "field": [rule_fn_or_tuple, ...], ... }
                        A tuple (rule_fn, label) overrides the default label.

    Returns
    -------
    errors : dict  — { "field": "error message" } — empty means all valid
    """
    errors = {}
    for field, field_rules in rules_map.items():
        value = data.get(field)
        for rule in field_rules:
            if isinstance(rule, tuple):
                fn, label = rule
                msg = fn(value, label)
            else:
                msg = rule(value)
            if msg:
                errors[field] = msg
                break  # first failure per field
    return errors
