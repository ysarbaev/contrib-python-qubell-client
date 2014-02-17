import requests
from requests.auth import HTTPBasicAuth
from qubell.api.private.exceptions import ApiError
from qubell.api.provider import route, play_auth


class Router(object):
    #todo: store on class level dict(user -> cook)
    def __init__(self, base_url, verify_ssl=False):
        #todo: add 'safe' mode to track code 200 in box

        self.base_url = base_url
        self.verify_ssl = verify_ssl

        self.is_connected = False
        self._cookies = None
        self._auth = None

    #todo: add integration test for this
    def connect(self, email, password):
        url = self.base_url + '/signIn'
        data = {
            'email': email,
            'password': password}
        with requests.session() as session:
            session.post(url=url, data=data, verify=self.verify_ssl)
            self._cookies = session.cookies

        if 'PLAY_SESSION' not in self._cookies:
            raise ApiError("Authentication failed, please check settings")

        self._auth = HTTPBasicAuth(email, password)
        self.is_connected = True

    @route("POST /signIn")
    def post_sign_in(self, body): pass

    @play_auth
    @route("POST /organizations{ctype}")
    def post_organization(self, data, cookies, ctype=".json"): pass

    @play_auth
    @route("GET /organizations{ctype}")
    def get_organizations(self, cookies, ctype=".json"): pass