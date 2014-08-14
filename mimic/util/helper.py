
"""
Helper methods
"""
from datetime import datetime, timedelta


fmt = '%Y-%m-%dT%H:%M:%S.%fZ'


def not_found_response(resource='servers'):
    """
    Return a 404 response body for Nova, depending on the resource.  Expects
    resource to be one of "servers", "images", or "flavors".

    If the resource is unrecognized, defaults to
    "The resource culd not be found."
    """
    message = {
        'servers': "Instance could not be found",
        'images': "Image not found.",
        'flavors': "The resource could not be found.",
        'loadbalancer': "Load balancer not found"
    }

    return {
        "itemNotFound": {
            "message": message.get(resource, "The resource could not be found."),
            "code": 404
        }
    }


def invalid_resource(message, response_code=400):
    """
    Returns the given message within in bad request body, and sets the response
    code to given response code. Defaults response code to 404, if not provided.
    """
    return {"message": message, "code": response_code}


def current_time_in_utc():
    """
    Returns current time in UTC in the format "%Y-%m-%dT%H:%M:%S.%fZ"
    """
    return datetime.utcnow().strftime(fmt)


def set_resource_status(updated_time, time_delta, status='ACTIVE'):
    """
    Given the updated_time and time delta, if the updated_time + time_delta is
    greater than the current time in UTC, returns the given status; otherwise
    return None.

    :param str updated_time: The time that the server was last updated by a
        client.
    :param int time_delta: The delta, in seconds, from ``updated_time``.
    :param str status: The status to return if the time_delta has expired (i.e.
        the wall clock has advanced more than ``time_delta`` past
        ``updated_time``).

    :return: ``status`` or ``None``.
    """
    if (datetime.strptime(updated_time, fmt) + timedelta(seconds=time_delta)) < \
            datetime.utcnow():
        return status
