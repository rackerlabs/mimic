"""
Model objects for the Identity Admin mimic
"""

from twisted.web.http import BAD_REQUEST


def _identity_admin_error_message(msg_type, message, status_code, request):
    """
    Set the response code on the request, and return a JSON blob representing
    a Identity Admin error body, in the format Identity Admin returns error
    messages.

    :param str msg_type: What type of error this is - something like
        "badRequest" or "itemNotFound" for Identity Admin.
    :param str message: The message to include in the body.
    :param int status_code: The status code to set
    :param request: the request to set the status code on

    :return: dictionary representing the error body
    """
    request.setResponseCode(status_code)
    return {
        msg_type: {
            "message": message,
            "code": status_code
        }
    }


def bad_request(message, request):
    """
    Return a 400 error body associated with a Identity Admin bad request error.
    Also sets the response code on the request.

    :param str message: The message to include in the bad request body.
    :param request: The request on which to set the response code.

    :return: dictionary representing the error body.
    """
    return _identity_admin_error_message("badRequest", message, BAD_REQUEST, request)
