from enum import Enum
from typing import Dict, List


class UserRole(str, Enum):
    """
    Enum defining user roles with increasing levels of permissions.
    """
    MEMBER = "member"
    TEAM_HEAD = "team_head"
    MANAGER = "manager"
    SUPER_ADMIN = "super_admin"


# Role hierarchy defining which roles can create/manage which other roles
ROLE_HIERARCHY: Dict[UserRole, List[UserRole]] = {
    UserRole.SUPER_ADMIN: [UserRole.SUPER_ADMIN, UserRole.MANAGER, UserRole.TEAM_HEAD, UserRole.MEMBER],
    UserRole.MANAGER: [UserRole.TEAM_HEAD, UserRole.MEMBER],
    UserRole.TEAM_HEAD: [UserRole.MEMBER],
    UserRole.MEMBER: []
}


def check_role_permissions(actor_role: UserRole, target_role: UserRole) -> bool:
    """
    Check if a user with actor_role has permission to manage users with target_role.
    
    Args:
        actor_role: Role of the user performing the action
        target_role: Role of the user being targeted
        
    Returns:
        bool: True if actor has permission to manage target, False otherwise
    """
    return target_role in ROLE_HIERARCHY[actor_role]


def can_list_users(user_role: UserRole) -> bool:
    """
    Check if a user with the given role can list all users.
    
    Args:
        user_role: Role of the user attempting to list users
        
    Returns:
        bool: True if the user can list all users, False otherwise
    """
    return user_role in [UserRole.SUPER_ADMIN, UserRole.MANAGER]