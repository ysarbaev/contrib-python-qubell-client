from mock import patch, Mock
import unittest

from qubell.api.private.exceptions import ApiUnauthorizedError
from qubell.api.provider.router import Router


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.router = Router("http://router.org")

    def test_no_connection_for_new(self):
        assert not self.router.is_connected

    def test_connection_identification(self):
        with patch.object(self.router, "_cookies", {"PLAY_SESSION": "any_val"}):
            assert self.router.is_connected

    def test_connection_fail_when_no_cookies(self):
        with patch.object(self.router, "_cookies", None):
            assert not self.router.is_connected

    def test_connection_fail_when_wrong_cookies(self):
        with patch.object(self.router, "_cookies", {"eat": "this"}):
            assert not self.router.is_connected

    def test_get_connected(self):
        cooka = {"PLAY_SESSION": "damn_cookie_mock"}

        def session_mock():
            session = Mock(cookies=cooka)
            session.__enter__ = lambda self: session
            session.__exit__ = Mock()
            return session

        with patch("requests.session", return_value=session_mock()):
            self.router.connect("any@where", "***")
        assert self.router.is_connected
        assert self.router._cookies == cooka
        # seems pretty fast, didn't mock
        assert self.router._auth.username == "any@where"
        assert self.router._auth.password == "***"


    def test_exception_if_not_get_connected(self):
        with self.assertRaises(ApiUnauthorizedError) as context, patch("requests.session"):
            self.router.connect("any@where", "**wrong**")
        assert str(context.exception) == "Authentication failed, please check settings"

