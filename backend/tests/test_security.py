import unittest

from security import get_token_from_request
from config import settings


class FakeRequest:
    def __init__(self, headers=None, cookies=None):
        self.headers = headers or {}
        self.cookies = cookies or {}


class SecurityTests(unittest.TestCase):
    def test_reads_configured_auth_cookie_name(self):
        original_cookie_name = settings.AUTH_COOKIE_NAME
        settings.AUTH_COOKIE_NAME = "custom_auth"

        try:
            token = get_token_from_request(
                FakeRequest(cookies={"custom_auth": "token-value"})
            )
        finally:
            settings.AUTH_COOKIE_NAME = original_cookie_name

        self.assertEqual(token, "token-value")

    def test_authorization_header_takes_precedence(self):
        token = get_token_from_request(
            FakeRequest(
                headers={"Authorization": "Bearer header-token"},
                cookies={settings.AUTH_COOKIE_NAME: "cookie-token"},
            )
        )

        self.assertEqual(token, "header-token")


if __name__ == "__main__":
    unittest.main()
