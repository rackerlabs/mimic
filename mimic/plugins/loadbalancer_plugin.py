"""
Plugin for Rackspace cloud load balancer mock.
"""
from mimic.rest.loadbalancer_api import LoadBalancerApi, LoadBalancerControlApi

loadbalancer = LoadBalancerApi()
loadbalancer_control = LoadBalancerControlApi(lb_api=loadbalancer)
