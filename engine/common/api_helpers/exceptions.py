from rest_framework.exceptions import APIException


class BadRequest(APIException):
    status_code = 400
    default_detail = "Your browser sent a request that this server could not understand"
    default_code = "bad_request"


class Unauthorized(APIException):
    status_code = 401
    default_detail = "Request could not be authenticated"
    default_code = "Unauthorized"


class Forbidden(APIException):
    status_code = 403
    default_detail = "You do not have permission to perform this action"
    default_code = "Forbidden"


class Conflict(APIException):
    status_code = 409
    default_detail = "duplicate record found"
    default_code = "Conflict"
