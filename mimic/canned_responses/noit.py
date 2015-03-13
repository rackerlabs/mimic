"""
Canned response for Noit
"""
import time
from mimic.canned_responses.noit_metrics_fixture import (metrics_common_template,
                                                         metrics)


noit_cache = {}


def noit_check_template(request):
    """
    Template used to create check.
    """
    check_template = {
        "check": {
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
            },
            "state": {
                "running": "false",
                "killed": "false",
                "configured": "true",
                "disabled": "false",
                "target_ip": "23.253.6.64",
                "last_run": {
                    "@now": "1422323039.361",
                    "#text": "1422323039.357"
                },
                "runtime": "0.958",
                "availability": "available",
                "state": "good",
                "status": "code=200,rt=0.957s,bytes=44779,sslerror",
                "metrics": [
                    {
                        "@type": "inprogress"
                    },
                    {
                        "@type": "current",
                        "@timestamp": str(time.time())
                    }
                ]
            }
        }
    }
    return check_template


def create_check(request, check_id):
    """
    Create the check and saves it in the cache.
    """
    noit_cache[check_id] = noit_check_template(request)
    return noit_cache[check_id]


def test_check(check_type):
    """
    Creates a response for test check
    """
    metrics_common_template["check"]["state"]["metrics"][1].update(metrics.get(check_type, {}))
    return metrics_common_template


def get_check(check_id):
    """
    Gets the check_id from noit_cache
    """
    return noit_cache[check_id]


def get_all_checks():
    """
    Gets all checks from noit_cache
    """
    get_all_check_common_template = {
        "checks": {
            "@resolve_targets": "true",
            "@max_initial_stutter": "30000",
            "@filterset": "default",
            "@transient_min_period": "1000",
            "@transient_period_granularity": "500",
            "@backingstore": "/tmp/noit-bs",
            "config": {
                "@xmlns:ip_acl": "noit://module/ip_acl",
                "ip_acl:whitelist": None
            }
        }
    }
    check_list = []
    for key, value in noit_cache.items():
        each_check = value["check"]["attributes"]
        each_check["uuid"] = key
        each_check["config"] = value["check"]["config"]
        check_list.append(each_check)
    get_all_check_common_template["checks"]["check"] = check_list
    return get_all_check_common_template


def delete_check(check_id):
    """
    Delete the check_id from noit cache
    """
    try:
        del noit_cache[check_id]
    except:
        return 404
    return
