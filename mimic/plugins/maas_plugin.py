"""
Plugin for Rax Monitoring API (aka MaaS, aka ele) mock.
"""
from mimic.rest.maas_api import MaasApi, MaasControlApi

maas = MaasApi()
maas_control = MaasControlApi(maas_api=maas)
