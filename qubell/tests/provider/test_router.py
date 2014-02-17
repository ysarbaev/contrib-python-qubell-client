from requests.cookies import cookiejar_from_dict

import unittest2
from mock import patch, Mock, MagicMock, PropertyMock

from qubell.api.provider import route, play_auth, basic_auth

from qubell.api.provider.router import Router

json_header = {'Content-Type': 'application/json'}

@patch("requests.request", create=True)
class RouterDecoratorTest(unittest2.TestCase):
    class DummyRouter(Router):
        @route("GET /simple")
        def get_simple(self): pass

        @route("GET /simple")
        def get_simple_with_return(self):
            return "this is won't be returned"

        @route("POST /simple")
        def post_simple(self, data): pass

        @route("GET /named/{prefix}{some_name}")
        def get_named(self, some_name, prefix="id"): pass

        @play_auth
        @route("POST /auth")
        def post_something_privetly(self, cookies): pass

        @basic_auth
        @route("POST /auth")
        def post_something_publicly(self, auth): pass

        @play_auth
        @route("GET /simple.json")
        def get_simple_json(self, cookies): pass

    router = DummyRouter("http://nowhere.com")
    router.is_connected = True



    def test_simple_get(self, request_mock):
        self.router.get_simple()
        request_mock.assert_called_once_with('GET', 'http://nowhere.com/simple', verify=False)

    def test_return_from_request(self, request_mock):
        ret_value = "anything from requests.request"
        request_mock.return_value = ret_value
        assert self.router.get_simple_with_return() == ret_value

    def test_simple_post(self, request_mock):
        self.router.post_simple(data="many data")
        request_mock.assert_called_once_with('POST', 'http://nowhere.com/simple', verify=False, data="many data")

    def test_parameters(self, request_mock):
        self.router.get_named(some_name="12345")
        request_mock.assert_called_once_with('GET', 'http://nowhere.com/named/id12345', verify=False)

    def test_parameter_without_name(self, request_mock):
        """Route parameters should be defined explicitly"""
        with self.assertRaises(AttributeError) as context:
            self.router.get_named("12345")
        assert context.exception.message == "Define 'some_name' as named argument for route."
        assert not request_mock.called

    def test_play_auth(self, request_mock):
        self.router._cookies = "Big Cake"
        self.router.post_something_privetly()
        request_mock.assert_called_once_with('POST', 'http://nowhere.com/auth', verify=False, cookies="Big Cake")

    def test_play_when_cookies_forced(self, request_mock):
        with self.assertRaises(AttributeError) as context:
            self.router.post_something_privetly(cookies="anything")
        assert context.exception.message == "don't set cookies explicitly"
        assert not request_mock.called

    def test_basic_auth(self, request_mock):
        self.router._auth = "Encoding..."
        self.router.post_something_publicly()
        request_mock.assert_called_once_with('POST', 'http://nowhere.com/auth', verify=False, auth="Encoding...", header = json_header)

    def test_basic_when_auth_forced(self, request_mock):
        with self.assertRaises(AttributeError) as context:
            self.router.post_something_publicly(auth="anything")
        assert context.exception.message == "don't set auth token explicitly"
        assert not request_mock.called

    def test_simple_json(self, request_mock):
        self.router.get_simple_json()
        request_mock.assert_called_once_with('GET', 'http://nowhere.com/simple.json', header = json_header, cookies="Big Cake", verify=False)