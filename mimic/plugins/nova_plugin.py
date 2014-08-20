"""
Plugin for OpenStack compute / Rackspace cloud server mock.
"""
from mimic.rest.nova_api import NovaApi, NovaErrorInjection

nova = NovaApi()
nova_control_plane = NovaErrorInjection(nova)
