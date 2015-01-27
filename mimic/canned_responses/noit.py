"""
Canned response for Nova
"""
from mimic.canned_responses.noit_metrics_fixture import (metrics_common_template,
                                                          metrics)

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


def test_check(check_type):
    """

    """
    if metrics_common_template["check"]["state"].get("metric"):
        del metrics_common_template["check"]["state"]["metric"]
    metrics_common_template["check"]["state"].update(metrics.get(check_type, {}))
    return metrics_common_template

def get_check(check_id):
    """
    Gets the check_id from noit_cache
    """
    return noit_cache[check_id]


def get_checks():
    """
    Gets all checks from noit_cache
    """
    return noit_cache


def delete_check(check_id):
    """
    Delete the check_id from noit cache
    """
    try:
        del noit_cache[check_id]
    except:
        return 404
    return
