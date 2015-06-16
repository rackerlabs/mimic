"""
A pseudo enumeration of errors seen from Rackspace Cloud Load Balancers.

Note: This is not a good way to make these available to users to specify, and
so the API will probably change.  But this seems better than sprinkling them
all over the request code right now.
"""


def considered_immutable_error(clb_state, lb_id):
    """
    This error is seen whenever the load balancer is not in an ACTIVE state,
    in which case it is immutable.  Any modifications to the load balancer
    (adding nodes, deleting nodes, changing nodes) will result in this
    message.

    Not sure if this message is applicable when deleting the load balancer.

    :param str clb_state: The states in which the CLB is considered immutable.
        The state should be one of (PENDING_DELETE, PENDING_UPDATE, ERROR).
        This state gets incorporated into the message.
    :param str lb_id: The load balancer ID, which gets incorporated into the
        message.

    :return: a `tuple` of (dict body message, http status code)
    """
    return (
        {
            "message": "Load Balancer '{0}' has a status of '{1}' and is "
                       "considered immutable.".format(lb_id, clb_state),
            "code": 422
        },
        422)
