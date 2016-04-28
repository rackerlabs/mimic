"""
Plugin for OpenStack compute / Rackspace cloud server mock.
"""
from mimic.rest.nova_api import NovaApi, NovaControlApi

nova = NovaApi()
nova_control_api = NovaControlApi(nova_api=nova)
