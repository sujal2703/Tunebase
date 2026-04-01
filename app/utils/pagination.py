from typing import Any, Dict, Tuple


def get_pagination_params(request) -> Tuple[int, int]:
    """
    Read `page` and `per_page` from query params with sane defaults.
    """
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 20))
    except (TypeError, ValueError):
        per_page = 20

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)
    return page, per_page


def make_pagination_meta(page: int, per_page: int, total: int) -> Dict[str, Any]:
    total_pages = (total + per_page - 1) // per_page if per_page else 0
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }

