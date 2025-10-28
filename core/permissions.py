
from utils.role_filter import *


def is_manager(user) -> bool:
    """
    Ověří, zda má uživatel v některé ze svých aktuálních rolí permission 'manager'.
    """
    if not user.is_authenticated:
        return False

    # vezmeme všechny platné MEMBER role uživatele
    roles = get_all_current_member_roles(user)

    # pokud mezi nimi existuje alespoň jedna s požadovanou permission, vrátíme True
    return roles.filter(role_permissions__name='manager').exists()


