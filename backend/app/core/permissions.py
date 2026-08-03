# This file is deprecated - use app.utils.permissions instead
# Kept for backward compatibility

from app.utils.permissions import (
    is_owner,
    is_admin,
    can_manage_workspace
)

__all__ = [
    'is_owner',
    'is_admin',
    'can_manage_workspace'
]