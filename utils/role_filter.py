from django.utils import timezone
from django.db.models import Q
from app.models import Role 

def get_all_current_member_roles(user):
    """
    Return all active Roles for user

    :param user: Instance request.user
    :return: Instance Role nebo None
    """
    if not user.is_authenticated:
        return {}
    
    return Role.objects.filter(
        account=user,
        index__isnull=False
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gt=timezone.now())
    )
