"""Default-deny role-based document authorization."""

from typing import Iterable, List

from secure_rag.auth.models import DocumentChunk, Role, UserIdentity


def can_access(identity: UserIdentity, chunk: DocumentChunk) -> bool:
    """Return whether an authenticated identity may retrieve a chunk."""

    if not identity.is_active:
        return False
    if identity.role is Role.ADMIN:
        return True
    return identity.role in chunk.allowed_roles


def filter_authorized_chunks(
    identity: UserIdentity,
    chunks: Iterable[DocumentChunk],
) -> List[DocumentChunk]:
    """Remove forbidden chunks before retrieval results reach an LLM."""

    return [chunk for chunk in chunks if can_access(identity, chunk)]

