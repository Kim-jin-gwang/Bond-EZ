from django.views.decorators.http import require_GET

from apps.common.responses import ok

from .selectors import beginner_bonds, latest_news, main_base_rates, main_credit_rating_rates, main_deposit_rates
from .serializers import serialize_home_payload


@require_GET
def main_summary(request):
    return ok(
        serialize_home_payload(
            bonds=beginner_bonds(),
            news=latest_news(),
            base_rates=main_base_rates(),
            deposit_rates=main_deposit_rates(),
            credit_rates=main_credit_rating_rates(),
        )
    )

