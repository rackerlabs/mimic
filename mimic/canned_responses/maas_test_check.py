"""
Canned response for /test-check
"""

import collections


def test_check(checkType):
    """
    Support test-check API
    """
    test_check_responses = collections.defaultdict(lambda: "")
    test_check_responses["agent.cpu"] = [
        {
            "timestamp": 0,
            "available": True,
            "status": "success",
            "metrics": {
                "user_percent_average": {
                    "data": 7.1695253641707,
                    "type": "n",
                    "unit": "percent"
                },
                "wait_percent_average": {
                    "data": 0,
                    "type": "n",
                    "unit": "percent"
                },
                "sys_percent_average": {
                    "data": 9.0368192996259,
                    "type": "n",
                    "unit": "percent"
                },
                "idle_percent_average": {
                    "data": 83.793655336203,
                    "type": "n",
                    "unit": "percent"
                },
                "irq_percent_average": {
                    "data": 0,
                    "type": "n",
                    "unit": "percent"
                },
                "usage_average": {
                    "data": 16.206344663797,
                    "type": "n",
                    "unit": "percent"
                },
                "min_cpu_usage": {
                    "data": 9.6645367412141,
                    "type": "n",
                    "unit": "percent"
                },
                "max_cpu_usage": {
                    "data": 22.748152586379,
                    "type": "n",
                    "unit": "percent"
                },
                "stolen_percent_average": {
                    "data": 0,
                    "type": "n",
                    "unit": "percent"
                }
            }
        }
    ]
    return test_check_responses[checkType]
