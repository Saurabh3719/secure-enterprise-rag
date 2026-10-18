"""Authentication and role-based authorization primitives."""

from secure_rag.auth.models import DocumentChunk, Role, UserIdentity, UserRecord
from secure_rag.auth.passwords import hash_password, verify_password
from secure_rag.auth.policy import can_access, filter_authorized_chunks
from secure_rag.auth.service import AuthenticationService, InMemoryUserRepository

__all__ = [
    "AuthenticationService",
    "DocumentChunk",
    "InMemoryUserRepository",
    "Role",
    "UserIdentity",
    "UserRecord",
    "can_access",
    "filter_authorized_chunks",
    "hash_password",
    "verify_password",
]

