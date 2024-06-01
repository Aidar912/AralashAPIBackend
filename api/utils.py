from .models import APIKey, User
from django.core.exceptions import ObjectDoesNotExist

def verify_key(auth_login, auth_secret):
    try:
        user = User.objects.get(email=auth_login)
        api_key = APIKey.objects.get(key=auth_secret, is_active=True, company__usercompanyrelation__user=user)
        return True, user, api_key.company
    except (ObjectDoesNotExist, ValueError):
        return False, None, None
