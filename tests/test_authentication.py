import unittest

from secure_rag.auth import AuthenticationService, InMemoryUserRepository, Role
from secure_rag.auth.passwords import hash_password, verify_password


class PasswordTests(unittest.TestCase):
    def test_hash_does_not_store_plaintext_password(self) -> None:
        password = "correct horse battery staple"
        stored_hash = hash_password(password)

        self.assertNotIn(password, stored_hash)
        self.assertTrue(verify_password(password, stored_hash))

    def test_same_password_gets_different_salts(self) -> None:
        first = hash_password("same password")
        second = hash_password("same password")

        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("same password", first))
        self.assertTrue(verify_password("same password", second))

    def test_wrong_password_is_rejected(self) -> None:
        stored_hash = hash_password("right password")

        self.assertFalse(verify_password("wrong password", stored_hash))


class AuthenticationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = InMemoryUserRepository()
        self.service = AuthenticationService(self.repository)

    def test_login_id_is_normalized_and_user_can_authenticate(self) -> None:
        self.service.register(" Engineer01 ", "a strong password", Role.ENGINEER)

        identity = self.service.authenticate("ENGINEER01", "a strong password")

        self.assertIsNotNone(identity)
        assert identity is not None
        self.assertEqual(identity.login_id, "engineer01")
        self.assertEqual(identity.role, Role.ENGINEER)
        self.assertFalse(hasattr(identity, "password_hash"))

    def test_duplicate_login_id_is_rejected(self) -> None:
        self.service.register("user01", "first password", Role.INTERN)

        with self.assertRaises(ValueError):
            self.service.register(" USER01 ", "second password", Role.ENGINEER)

    def test_unknown_login_id_and_wrong_password_have_same_result(self) -> None:
        self.service.register("hr01", "correct password", Role.HR)

        self.assertIsNone(self.service.authenticate("missing", "correct password"))
        self.assertIsNone(self.service.authenticate("hr01", "wrong password"))


if __name__ == "__main__":
    unittest.main()

