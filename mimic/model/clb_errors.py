"""
A pseudo enumeration of errors seen from Rackspace Cloud Load Balancers.

Note: This is not a good way to make these available to users to specify, and
so the API will probably change.  But this seems better than sprinkling them
all over the request code right now.
"""


def considered_immutable_error(clb_state, lb_id):
    """
    Return the error seen whenever the load balancer is not in an ACTIVE state,
    in which case it is immutable.  Any modifications to the load balancer
    (adding nodes, deleting nodes, changing nodes) will result in this
    message.

    Not sure if this message is applicable when deleting the load balancer.

    :param str clb_state: The states in which the CLB is considered immutable.
        The state should be one of (PENDING_DELETE, PENDING_UPDATE, ERROR).
        This state gets incorporated into the message.
    :param str lb_id: The load balancer ID, which gets incorporated into the
        message.

    :return: a `tuple` of (dict body message, 422 http status code)
    """
    return (
        {
            "message": "Load Balancer '{0}' has a status of '{1}' and is "
                       "considered immutable.".format(lb_id, clb_state),
            "code": 422
        },
        422)


def updating_node_validation_error(address=False, port=False, id=False,
                                   weight=False):
    """
    Verified 2015-06-16:

    - when trying to update a CLB node's address/port/id, which are
      immutable.
    - when trying to update a CLB node's weight to be < 1 or > 100

    At least one of address, port, id, and weight should be `True` for this
    error to apply.

    :param bool address: Whether the address was passed to update
    :param bool port: Whether the port was passed to update
    :param bool id: Whether the ID was passed to update
    :param bool weight: Whether the weight was passed to update and wrong

    :return: a `tuple` of (dict body message, 400 http status code)
    """
    messages = []
    if address:
        messages.append("Node ip field cannot be modified.")
    if port:
        messages.append("Port field cannot be modified.")
    if weight:
        messages.append("Node weight is invalid. Range is 1-100. "
                        "Please specify a valid weight.")
    if id:
        messages.append("Node id field cannot be modified.")

    return(
        {
            "validationErrors": {
                "messages": messages
            },
            "message": "Validation Failure",
            "code": 400,
            "details": "The object is not valid"
        },
        400
    )


def invalid_json_schema():
    """
    Verified 2015-06-16 for creating a LB, changing a node, adding nodes:

    - when providing invalid fields in the JSON request
    - when providing invalid JSON
    - this schema validation happens even before checking whether a LB and/or
      node exists

    :return: a `tuple` of (dict body message, 400 http status code)
    """
    return(
        {
            "message": ["JSON does not match the expected schema"]
        },
        400
    )


def node_not_found():
    """
    Verified 2015-06-16 for updating a node that does not exist.

    :return: a `tuple` of (dict body message, 404 http status code)
    """
    return (
        {
            "message": "Node not found",
            "code": 404
        },
        404
    )


def loadbalancer_not_found():
    """
    Verified 2015-06-16:
    - when trying to update a CLB node on a CLB that doesn't exist

    :return: a `tuple` of (dict body message, 404 http status code)
    """
    return (
        {
            "message": "Load balancer not found",
            "code": 404
        },
        404
    )


def not_found_xml(item):
    """
    Return XML representation of CLB item not found.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<itemNotFound xmlns="http://docs.openstack.org/loadbalancers/api/v1.0" code="404">'
        '<message>{0} not found</message></itemNotFound>').format(item), 404


def lb_deleted_xml():
    """
    Return XML representation of CLB marked as DELETED
    """
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<message xmlns="http://docs.openstack.org/loadbalancers/api/v1.0" code="410">'
        'The loadbalancer is marked as deleted.</message>'), 410
