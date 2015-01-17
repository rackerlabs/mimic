"""
Canned response for Nova
"""

noit_cache = {}


def noit_check_template(request):
    """
    Template used to create check.
    """
    check_template = {
        "attributes": {
            "name": request["name"],
            "module": request["module"],
            "target": request["target"],
            "period": request["period"],
            "timeout": request["timeout"],
            "filterset": request["filterset"]
        },
        "config": {
            "code": ".*",
            "header_123key.test": "400",
            "header_message123": "test",
            "method": "GET",
            "url": "http://127.0.0.1:32321/.well-known/404",
            "redirects": 10,
            "read_limit": 4567777
        }
    }
    return check_template


def create_check(request, check_id):
    """
    Create the check and saves it in the cache.
    """
    noit_cache[check_id] = noit_check_template(request)
    # construct xml response and return it

    return


def get_check(check_id):
    """
    Gets the check_id from noit_cache
    """
    return noit_cache[check_id]


def get_checks(check_id):
    """
    Gets all checks from noit_cache
    """
    return noit_cache
