"""Login orchestration separated from storage and password hashing."""

from typing import Dict, Optional

from secure_rag.auth.models import Role, UserIdentity, UserRecord
from secure_rag.auth.passwords import hash_password, verify_password


def normalize_login_id(login_id: str) -> str:
    """Create the canonical form used for account lookup."""

    normalized = login_id.strip().lower()
    if not normalized:
        raise ValueError("login_id must not be empty")
    return normalized


class InMemoryUserRepository:
    """Temporary repository used until PostgreSQL is introduced."""

    def __init__(self) -> None:
        self._users: Dict[str, UserRecord] = {}

    def add(self, user: UserRecord) -> None:
        if user.login_id in self._users:
            raise ValueError("login_id already exists")
        self._users[user.login_id] = user

    def find_by_login_id(self, login_id: str) -> Optional[UserRecord]:
        return self._users.get(normalize_login_id(login_id))


class AuthenticationService:
    """Registers accounts and turns valid credentials into safe identities."""

    def __init__(self, users: InMemoryUserRepository) -> None:
        self._users = users
        # Missing accounts still perform one expensive password verification so
        # response timing reveals less information about which login IDs exist.
        self._dummy_password_hash = hash_password("authentication timing sentinel")

    def register(self, login_id: str, password: str, role: Role) -> UserIdentity:
        normalized_login_id = normalize_login_id(login_id)
        record = UserRecord(
            login_id=normalized_login_id,
            password_hash=hash_password(password),
            role=role,
        )
        self._users.add(record)
        return UserIdentity(login_id=record.login_id, role=record.role)

    def authenticate(self, login_id: str, password: str) -> Optional[UserIdentity]:
        user = self._users.find_by_login_id(login_id)
        stored_hash = (
            user.password_hash
            if user is not None and user.is_active
            else self._dummy_password_hash
        )
        password_is_valid = verify_password(password, stored_hash)

        if user is None or not user.is_active or not password_is_valid:
            return None
        return UserIdentity(
            login_id=user.login_id,
            role=user.role,
            is_active=user.is_active,
        )

