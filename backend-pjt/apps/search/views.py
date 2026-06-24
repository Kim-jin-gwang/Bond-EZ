from django.views.decorators.http import require_GET

from apps.accounts.services import record_search_log
from apps.common.responses import ok

from .bonds import SearchUnavailable, fallback_search_bonds, search_bonds


@require_GET
def bond_search(request):
    if not request.session.session_key:
        request.session.create()
    record_search_log(request.user, request.session.session_key, request.GET)
    try:
        payload = search_bonds(request.GET)
    except Exception:
        payload = fallback_search_bonds(request.GET)

    return ok(payload)

