from random import randrange
from twisted.python import log
from datetime import datetime


server_addresses_cache = {}
s_cache = {}


def not_found_response(resource='servers'):
    """
    Return a 404 response body for Nova, depending on the resource.  Expects
    resource to be one of "servers", "images", or "flavors".

    If the resource is unrecognized, defaults to
    "The resource culd not be found."
    """
    message = {
        'servers': "Instance could not be found",
        'images': "Image not found.",
        'flavors': "The resource could not be found."
    }

    return {
        "itemNotFound": {
            "message": message.get(resource, "The resource could not be found."),
            "code": 404
        }
    }


def server_template(tenant_id, server_info, server_id):
    """
    Template used to create server cache.
    """
    server_template = {
        "OS-DCF:diskConfig": server_info['OS-DCF:diskConfig'] or "AUTO",
        "OS-EXT-STS:power_state": 1,
        "OS-EXT-STS:task_state": "null",
        "OS-EXT-STS:vm_state": "active",
        "accessIPv4": "198.101.241.238",
        "accessIPv6": "2001:4800:780e:0510:d87b:9cbc:ff04:513a",
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
        "created": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        "flavor": {
            "id": server_info['flavorRef'],
            "links": [
                {
                    "href": "http://localhost:8902/{0}/flavors/{1}".format(tenant_id,
                                                                           server_info['flavorRef']),
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
                                                                        server_info['imageRef']),
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
        "status": "ACTIVE",
        "tenant_id": tenant_id,
        "updated": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        "user_id": "170454"
    }
    return server_template


def create_server(tenant_id, server_info, server_id):
    """
    Canned response for create server and adds the server to the server cache.
    """
    s_cache[server_id] = server_template(tenant_id, server_info, server_id)
    log.msg(s_cache)
    return {'server': {"OS-DCF:diskConfig": s_cache[server_id]['OS-DCF:diskConfig'],
                       "id": s_cache[server_id]['id'],
                       "links": s_cache[server_id]['links'],
                       "adminPass": "testpassword"}}, 201


def get_server(server_id):
    """
    Verify if the given server_id exists in the server cache. If true, return server
    data else return None
    """
    if server_id in s_cache:
        return {'server': s_cache[server_id]}, 200
    else:
        return not_found_response(), 404


def list_server(tenant_id, name=None, details=True):
    """
    Return a list of all servers in  the server cache with the given tenant_id
    """
    response = {k: v for (k, v) in s_cache.items() if tenant_id == v['tenant_id']}
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
    Canned response for get image.
    The image id provided is substituted in the response
    """
    return {'image': {'status': 'ACTIVE', 'id': image_id}}


def get_flavor(flavor_id):
    """
    Canned response for get flavor.
    The flavor id provided is substituted in the response
    """
    return {'flavor': {'name': '512MB Standard Instance',
                       'id': flavor_id}}


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
