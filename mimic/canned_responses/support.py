"""
Cannned responses for support
"""


def get_support_info(tenant_id):
    """
    Canned response for support
    """
    return {"service_type": "legacy", "service_level": "infrastructure", "id": tenant_id, "account_plan_request": None}