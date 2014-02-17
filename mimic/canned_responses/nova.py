from random import randrange
from mimic.canned_responses.mimic_presets import get_presets
from mimic.util.helper import (not_found_response, invalid_resource,
                               current_time_in_utc, set_resource_status)
import json


server_addresses_cache = {}
s_cache = {}
fmt = '%Y-%m-%dT%H:%M:%S.%fZ'


def server_template(tenant_id, server_info, server_id, status):
    """
    Template used to create server cache.
    """
    server_template = {
        "OS-DCF:diskConfig": "AUTO",
        "OS-EXT-STS:power_state": 1,
        "OS-EXT-STS:task_state": None,
        "OS-EXT-STS:vm_state": "active",
        "accessIPv4": "198.101.241.238",
        "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
        "key_name": None,
        "addresses": {
            "private": [
                {
                    "addr": "10.180.3.{0}".format(randrange(255)),
                    "version": 4
                }
            ],
            "public": [
                {
                    "addr": "198.101.241.{0}".format(randrange(255)),
                    "version": 4
                },
                {
                    "addr": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
                    "version": 6
                }
            ]
        },
        "created": current_time_in_utc(),
        "flavor": {
            "id": server_info['flavorRef'],
            "links": [
                {
                    "href": "http://localhost:8902/{0}/flavors/{1}".format(tenant_id,
                                                                           server_info[
                                                                               'flavorRef']),
                    "rel": "bookmark"
                }
            ]
        },
        "hostId": "33ccb6c82f3625748b6f2338f54d8e9df07cc583251e001355569056",
        "id": server_id,
        "image": {
            "id": server_info['imageRef'],
            "links": [
                {
                  "href": "http://localhost:8902/{0}/images/{1}".format(tenant_id,
                                                                        server_info[
                                                                            'imageRef']),
                  "rel": "bookmark"
                }
            ]
        },
        "links": [
            {
                "href": "http://localhost:8902/v2/{0}/servers/{1}".format(tenant_id, server_id),
                "rel": "self"
            },
            {
                "href": "http://localhost:8902/{0}/servers/{1}".format(tenant_id, server_id),
                "rel": "bookmark"
            }
        ],
        "metadata": server_info['metadata'],
        "name": server_info['name'],
        "progress": 100,
        "status": status,
        "tenant_id": tenant_id,
        "updated": current_time_in_utc(),
        "user_id": "170454"
    }
    return server_template


def create_server(tenant_id, server_info, server_id):
    """
    Canned response for create server and adds the server to the server cache.
    """
    status = "ACTIVE"
    if 'create_server_failure' in server_info['metadata']:
        dict_meta = json.loads(server_info['metadata']['create_server_failure'])
        return invalid_resource(dict_meta['message'], dict_meta['code']), dict_meta['code']

    if 'server_building' in server_info['metadata']:
        status = "BUILD"

    if 'server_error' in server_info['metadata']:
        status = "ERROR"

    s_cache[server_id] = server_template(
        tenant_id, server_info, server_id, status)
    return {
        'server': {"OS-DCF:diskConfig": s_cache[server_id]['OS-DCF:diskConfig'],
                   "id": s_cache[server_id]['id'],
                   "links": s_cache[server_id]['links'],
                   "adminPass": "testpassword"}}, 202


def get_server(server_id):
    """
    Verify if the given server_id exists in the server cache. If true, return server
    data else return None
    """
    if server_id in s_cache:
        set_server_state(server_id)
        return {'server': s_cache[server_id]}, 200
    else:
        return not_found_response(), 404


def list_server(tenant_id, name=None, details=True):
    """
    Return a list of all servers in the server cache with the given tenant_id
    """
    response = {k: v for (k, v) in s_cache.items() if tenant_id == v['tenant_id']}
    for each in response:
        set_server_state(each)
    if name:
        response = {k: v for (k, v) in response.items() if name in v['name']}
    if details:
        return {'servers': [values for values in response.values()]}, 200
    else:
        return {'servers': [{'name': values['name'], 'links':values['links'], 'id':values['id']}
                for values in response.values()]}, 200


def delete_server(server_id):
    """
    Returns True if the server was deleted from the cache, else returns false.
    """
    if server_id in s_cache:
        if 'delete_server_failure' in s_cache[server_id]['metadata']:
            del_meta = json.loads(s_cache[server_id]['metadata']['delete_server_failure'])
            if del_meta['times'] != 0:
                del_meta['times'] = del_meta['times'] - 1
                s_cache[server_id]['metadata']['delete_server_failure'] = json.dumps(del_meta)
                return invalid_resource('server error', del_meta['code']), del_meta['code']
        del s_cache[server_id]
        return True, 204
    else:
        return not_found_response(), 404


def list_addresses(server_id):
    """
    Returns the public and private ip address for the given server
    """
    if server_id in s_cache:
        return {'addresses': s_cache[server_id]['addresses']}, 200
    else:
        return not_found_response(), 404


def get_image(image_id):
    """
    Canned response for get image. The image id provided is substituted in the response,
    if not one of the invalid image ids specified in mimic_presets.
    """
    if any([image_id in get_presets['servers']['invalid_image_ref'], image_id.endswith('Z')]):
        return invalid_resource('Invalid imageRef provided.', 400), 400
    return {'image': {'status': 'ACTIVE', 'id': image_id}}, 200


def get_flavor(flavor_id):
    """
    Canned response for get flavor.
    The flavor id provided is substituted in the response
    """
    if flavor_id in get_presets['servers']['invalid_flavor_ref']:
        return invalid_resource('Invalid flavorRef provided.', 400), 400
    return {'flavor': {'name': '512MB Standard Instance',
                       'id': flavor_id}}, 200


def get_limit():
    """
    Canned response for limits for servers. Returns only the absolute limits
    """
    return {"limits":
            {"absolute": {"maxServerMeta": 40,
                          "maxPersonality": 5,
                          "totalPrivateNetworksUsed": 0,
                          "maxImageMeta": 40,
                          "maxPersonalitySize": 1000,
                          "maxSecurityGroupRules": -1,
                          "maxTotalKeypairs": 100,
                          "totalCoresUsed": 5,
                          "totalRAMUsed": 2560,
                          "totalInstancesUsed": 5,
                          "maxSecurityGroups": -1,
                          "totalFloatingIpsUsed": 0,
                          "maxTotalCores": -1,
                          "totalSecurityGroupsUsed": 0,
                          "maxTotalPrivateNetworks": 3,
                          "maxTotalFloatingIps": -1,
                          "maxTotalInstances": 200,
                          "maxTotalRAMSize": 256000}}}


def set_server_state(server_id):
    """
    If the server status is not active, sets the state of the server based on the
    server metadata
    """
    if s_cache[server_id]['status'] != "ACTIVE":
            if 'server_building' in s_cache[server_id]['metadata']:
                status = set_resource_status(
                    s_cache[server_id]['updated'],
                    int(s_cache[server_id]['metadata']['server_building']))
                s_cache[server_id]['status'] = status or s_cache[server_id]['status']
