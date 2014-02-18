import requests
from requests.auth import HTTPBasicAuth

from qubell.api.private.exceptions import ApiUnauthorizedError
from qubell.api.provider import route, play_auth


class Router(object):
    #todo: store on class level dict(user -> cook)
    def __init__(self, base_url, verify_ssl=False, verify_codes=True):
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.verify_codes = verify_codes

        self._cookies = None
        self._auth = None

    @property
    def is_connected(self):
        return 'PLAY_SESSION' in self._cookies

    #todo: add integration test for this
    def connect(self, email, password):
        url = self.base_url + '/signIn'
        data = {
            'email': email,
            'password': password}
        with requests.session() as session:
            session.post(url=url, data=data, verify=self.verify_ssl)
            self._cookies = session.cookies

        if not self.is_connected:
            raise ApiUnauthorizedError("Authentication failed, please check settings")

        self._auth = HTTPBasicAuth(email, password)

    @route("POST /signIn")
    def post_sign_in(self, body): pass

    @play_auth
    @route("POST /organizations{ctype}")
    def post_organization(self, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations{ctype}")
    def get_organizations(self, cookies, ctype=".json"): pass