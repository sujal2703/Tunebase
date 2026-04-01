import base64
import datetime as dt
import decimal
from typing import Any, Dict


def json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(value)).decode("ascii")
    return str(value)


def row_to_dict(row: Any) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy ORM instance or Row into JSON-serializable dict.
    """
    if row is None:
        return {}
    if hasattr(row, "__table__"):
        return {col.name: json_safe(getattr(row, col.name)) for col in row.__table__.columns}

    # Fallback for SQLAlchemy Row/tuple-like objects
    if hasattr(row, "_mapping"):
        return {k: json_safe(v) for k, v in row._mapping.items()}

    # Last resort: stringify
    return {"value": json_safe(row)}

