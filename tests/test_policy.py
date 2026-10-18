import unittest

from secure_rag.auth import (
    DocumentChunk,
    Role,
    UserIdentity,
    can_access,
    filter_authorized_chunks,
)


def chunk(chunk_id: str, *roles: Role) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id=f"document-{chunk_id}",
        content=f"Content for {chunk_id}",
        allowed_roles=frozenset(roles),
    )


class AuthorizationPolicyTests(unittest.TestCase):
    def test_every_configured_role_has_the_expected_value(self) -> None:
        self.assertEqual(
            {role.value for role in Role},
            {"intern", "engineer", "hr", "finance", "admin"},
        )

    def test_user_can_access_explicitly_allowed_chunk(self) -> None:
        engineer = UserIdentity("engineer01", Role.ENGINEER)
        runbook = chunk("runbook", Role.ENGINEER, Role.INTERN)

        self.assertTrue(can_access(engineer, runbook))

    def test_user_cannot_access_another_departments_chunk(self) -> None:
        engineer = UserIdentity("engineer01", Role.ENGINEER)
        payroll = chunk("payroll", Role.HR, Role.FINANCE)

        self.assertFalse(can_access(engineer, payroll))

    def test_empty_acl_is_denied_by_default(self) -> None:
        hr_user = UserIdentity("hr01", Role.HR)
        unclassified = chunk("unclassified")

        self.assertFalse(can_access(hr_user, unclassified))

    def test_admin_can_access_all_chunks(self) -> None:
        admin = UserIdentity("admin01", Role.ADMIN)

        self.assertTrue(can_access(admin, chunk("unclassified")))
        self.assertTrue(can_access(admin, chunk("finance", Role.FINANCE)))

    def test_inactive_user_is_denied_even_if_role_matches(self) -> None:
        inactive_hr = UserIdentity("former-hr", Role.HR, is_active=False)

        self.assertFalse(can_access(inactive_hr, chunk("handbook", Role.HR)))

    def test_filter_removes_forbidden_chunks(self) -> None:
        intern = UserIdentity("intern01", Role.INTERN)
        chunks = [
            chunk("onboarding", Role.INTERN, Role.ENGINEER),
            chunk("engineering", Role.ENGINEER),
            chunk("payroll", Role.HR, Role.FINANCE),
        ]

        visible = filter_authorized_chunks(intern, chunks)

        self.assertEqual([item.chunk_id for item in visible], ["onboarding"])


if __name__ == "__main__":
    unittest.main()
