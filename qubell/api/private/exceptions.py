__author__ = 'Khomenko'

class BaseQubellException(Exception): pass
    # def __init__(self, value):
    #     self.value = value
    # def __str__(self):
    #     return repr(self.value)

class NotFoundError(BaseQubellException): pass

class ExistsError(BaseQubellException): pass

class NotEnoughParams(BaseQubellException): pass

class ApiError(BaseQubellException): pass

class ApiUnauthorizedError(ApiError): pass

class ApiAuthenticationError(ApiError): pass

class ApiNotFoundError(ApiError): pass

api_http_code_errors = {401: ApiUnauthorizedError, 403: ApiAuthenticationError, 404: ApiNotFoundError}