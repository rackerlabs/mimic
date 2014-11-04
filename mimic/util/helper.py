
"""
Helper methods

:var fmt: strftime format for datetimes used in JSON.
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
        'loadbalancer': "Load balancer not found",
        'node': "Node not found"
    }
    resp = {
        "itemNotFound": {
            "message": message.get(resource, "The resource could not be found."),
            "code": 404
        }
    }
    if resource == 'loadbalancer' or resource == 'node':
        return resp["itemNotFound"]
    return resp


def invalid_resource(message, response_code=400):
    """
    Returns the given message within in bad request body, and sets the response
    code to given response code. Defaults response code to 404, if not provided.
    """
    return {"message": message, "code": response_code}


def set_resource_status(updated_time, time_delta, status='ACTIVE',
                        current_timestamp=None):
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
    :param float current_timestamp: The current time, in seconds from the POSIX
        epoch.

    :return: ``status`` or ``None``.
    """
    current_datetime = datetime.utcfromtimestamp(current_timestamp)
    last_updated_datetime = datetime.strptime(updated_time, fmt)
    expiration_interval = timedelta(seconds=int(time_delta))
    expiration_datetime = last_updated_datetime + expiration_interval

    if current_datetime >= expiration_datetime:
        return status
