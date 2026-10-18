"""Data models used by authentication and authorization."""

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class Role(str, Enum):
    """The five roles supported by the first RBAC model."""

    INTERN = "intern"
    ENGINEER = "engineer"
    HR = "hr"
    FINANCE = "finance"
    ADMIN = "admin"


@dataclass(frozen=True)
class UserRecord:
    """Stored account data.

    The original password is intentionally absent. Only its password hash is
    persisted. A record is internal data and must not be returned by an API.
    """

    login_id: str
    password_hash: str
    role: Role
    is_active: bool = True


@dataclass(frozen=True)
class UserIdentity:
    """Safe authenticated identity passed to authorization code."""

    login_id: str
    role: Role
    is_active: bool = True


@dataclass(frozen=True)
class DocumentChunk:
    """A searchable passage and the roles permitted to retrieve it."""

    chunk_id: str
    document_id: str
    content: str
    allowed_roles: FrozenSet[Role]

