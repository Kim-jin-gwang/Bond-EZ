from apps.bonds.serializers import date_or_none, number_or_none, serialize_bond_list_item


def serialize_user_bond(user_bond):
    return {
        "user_bond_id": user_bond.id,
        "bond": serialize_bond_list_item(user_bond.bond),
        "purchase_price": number_or_none(user_bond.purchase_price),
        "purchase_date": date_or_none(user_bond.purchase_date),
        "quantity": user_bond.quantity,
        "created_at": user_bond.created_at.isoformat() if user_bond.created_at else None,
    }

