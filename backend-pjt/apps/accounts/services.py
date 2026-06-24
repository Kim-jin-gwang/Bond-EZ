from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction


def create_user(data):
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    password_confirm = data.get("password_confirm") or ""

    if not username:
        return None, ("REQUIRED_FIELD_MISSING", "username은 필수입니다.", {"field": "username"})
    if not email:
        return None, ("REQUIRED_FIELD_MISSING", "email은 필수입니다.", {"field": "email"})
    if not password:
        return None, ("REQUIRED_FIELD_MISSING", "password는 필수입니다.", {"field": "password"})
    if password != password_confirm:
        return None, ("PASSWORD_CONFIRM_MISMATCH", "비밀번호 확인이 일치하지 않습니다.", {"field": "password_confirm"})
    if User.objects.filter(username=username).exists():
        return None, ("USERNAME_ALREADY_EXISTS", "이미 사용 중인 사용자 이름입니다.", {"field": "username"})
    if User.objects.filter(email=email).exists():
        return None, ("EMAIL_ALREADY_EXISTS", "이미 사용 중인 이메일입니다.", {"field": "email"})

    user = User(username=username, email=email)
    user.first_name = data.get("first_name", "")
    user.last_name = data.get("last_name", "")

    try:
        validate_password(password, user=user)
    except ValidationError as exc:
        return None, ("INVALID_PASSWORD", "비밀번호가 정책에 맞지 않습니다.", {"messages": exc.messages})

    with transaction.atomic():
        user.set_password(password)
        user.save()

    return user, None


def login_user(request, data):
    username_or_email = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not username_or_email:
        return None, ("REQUIRED_FIELD_MISSING", "username 또는 email은 필수입니다.", {"field": "username"})
    if not password:
        return None, ("REQUIRED_FIELD_MISSING", "password는 필수입니다.", {"field": "password"})

    username = username_or_email
    if "@" in username_or_email:
        user = User.objects.filter(email=username_or_email).first()
        username = user.username if user else username_or_email

    user = authenticate(request, username=username, password=password)
    if user is None:
        return None, ("INVALID_CREDENTIALS", "아이디 또는 비밀번호가 올바르지 않습니다.", {})
    if not user.is_active:
        return None, ("INACTIVE_USER", "비활성화된 사용자입니다.", {})

    login(request, user)
    return user, None


def logout_user(request):
    logout(request)


def update_user(user, data):
    allowed_fields = ["email", "first_name", "last_name"]
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data.get(field) or "")

    if "email" in data and User.objects.exclude(id=user.id).filter(email=user.email).exists():
        return ("EMAIL_ALREADY_EXISTS", "이미 사용 중인 이메일입니다.", {"field": "email"})

    password = data.get("password")
    password_confirm = data.get("password_confirm")
    if password:
        if password != password_confirm:
            return ("PASSWORD_CONFIRM_MISMATCH", "비밀번호 확인이 일치하지 않습니다.", {"field": "password_confirm"})
        try:
            validate_password(password, user=user)
        except Exception as e:
            msg = getattr(e, "messages", [str(e)])[0]
            return ("PASSWORD_VALIDATION_FAILED", msg, {"field": "password"})
        user.set_password(password)

    user.save()
    return None


from .models import UserSearchLog

def record_search_log(user, session_key, params):
    keyword = (params.get("keyword") or params.get("q") or "").strip()
    
    filters = {}
    filter_keys = [
        "bond_type", "credit_rating", "rating_group", "issuer_id", 
        "industry_id", "seniority", "guarantee_status", "option_type", 
        "interest_type", "payment_cycle_months", "maturity_from", 
        "maturity_to", "min_coupon", "max_coupon"
    ]
    for key in filter_keys:
        value = params.get(key)
        if value:
            if isinstance(value, str):
                value = value.strip()
            filters[key] = value
            
    if keyword or filters:
        db_user = user if (user and user.is_authenticated) else None
        UserSearchLog.objects.create(
            user=db_user,
            session_key=session_key,
            keyword=keyword or None,
            filters=filters
        )


