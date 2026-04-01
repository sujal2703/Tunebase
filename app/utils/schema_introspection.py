from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Type


def _normalize_name(name: str) -> str:
    # Normalize for fuzzy matching across snake_case/camelCase differences.
    # Example: "user_id" -> "userid"
    return "".join(ch for ch in name.lower() if ch.isalnum())


def column_names(model_cls: Any) -> List[str]:
    return [c.name for c in getattr(model_cls, "__table__", []).columns]


def find_column(model_cls: Any, candidates: Sequence[str], *, required: bool = True) -> Any:
    """
    Find a SQLAlchemy column on `model_cls` by candidate names with fuzzy normalization.
    """
    table = getattr(model_cls, "__table__", None)
    if table is None:
        raise ValueError(f"Model {model_cls} has no __table__")

    cols = { _normalize_name(col.name): col for col in table.columns }
    for cand in candidates:
        n = _normalize_name(cand)
        if n in cols:
            return cols[n]

    if required:
        raise ValueError(
            f"Required column not found on {table.name}. Candidates={list(candidates)}. "
            f"Available={table.columns.keys()}"
        )
    return None


def primary_key_column(model_cls: Any) -> Any:
    pks = list(getattr(model_cls, "__table__", []).primary_key.columns)
    if not pks:
        raise ValueError(f"No primary key found for model {getattr(model_cls, '__tablename__', model_cls)}")
    if len(pks) > 1:
        # For composite keys, return the first; endpoints requiring single-id will need schema adjustment.
        return pks[0]
    return pks[0]


def pick_created_at_column(model_cls: Any) -> Optional[Any]:
    candidates = ["created_at", "created", "createdon", "created_on", "signup_date", "login_time", "inserted_at"]
    try:
        return find_column(model_cls, candidates, required=False)
    except Exception:
        return None


def get_table_name(model_cls: Any) -> str:
    return getattr(model_cls, "__tablename__", getattr(model_cls, "name", ""))


def find_foreign_key_columns_referencing(model_cls: Any, referred_table: str) -> List[Any]:
    """
    Returns model columns that have foreign keys referencing `referred_table`.
    """
    table = getattr(model_cls, "__table__", None)
    if table is None:
        return []
    res: List[Any] = []
    for col in table.columns:
        for fk in col.foreign_keys:
            try:
                if fk.column.table.name == referred_table:
                    res.append(col)
                    break
            except Exception:
                continue
    return res


def model_to_dict(model_cls: Any, instance: Any) -> Dict[str, Any]:
    """
    Convert an ORM instance into a dict by introspecting its mapped columns.
    """
    table = getattr(model_cls, "__table__", None)
    if table is None or instance is None:
        return {}
    return {c.name: getattr(instance, c.name) for c in table.columns}

