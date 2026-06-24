from django.views.decorators.http import require_GET

from apps.common.responses import ok

from .bonds import SearchUnavailable, fallback_search_bonds, search_bonds


@require_GET
def bond_search(request):
    try:
        payload = search_bonds(request.GET)
    except Exception:
        payload = fallback_search_bonds(request.GET)

    return ok(payload)
