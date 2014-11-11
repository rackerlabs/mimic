# -*- test-case-name: mimic.test.test_loadbalancer -*-
"""
Canned response for fastly
"""

fastly_cache = {}
meta_cache = {}


def get_current_customer():
    """
    Returns the current customer with response code 200.

    :return: a JSON-serializable dictionary matching the format of the JSON
             response for fastly_client.get_current_customer()
             ("/current_customer") request.
    """
    current_customer = {
        u'can_edit_matches': u'0',
        u'can_read_public_ip_list': u'0', u'can_upload_vcl': u'1',
        u'updated_at': u'2014-11-03T23:37:44+00:00', u'has_config_panel': u'1',
        u'has_improved_ssl_config': False, u'id': u'2aJQHNECARTtoUMPKbVmU6',
        u'has_historical_stats': u'1', u'has_openstack_logging': u'0',
        u'can_configure_wordpress': u'0', u'has_improved_logging': u'1',
        u'readonly': '', u'ip_whitelist': u'0.0.0.0/0',
        u'owner_id': u'2b0qKpRnLnCKyMztZqkQvy',
        u'phone_number': u'770-813-1650', u'postal_address': None,
        u'billing_ref': None, u'can_reset_passwords': True,
        u'has_improved_security': u'1', u'stripe_account': None,
        u'name': u'Rackspace Hosting- Test',
        u'created_at': u'2014-11-03T23:37:43+00:00',
        u'can_stream_syslog': u'1', u'pricing_plan': u'developer',
        u'billing_contact_id': None, u'has_streaming': u'1'}
    return current_customer, 200
