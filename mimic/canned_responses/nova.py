from random import randrange
server_addresses_cache = {}


def get_server(tenant_id, server_info):
    """
    Canned response for get server.
    The server id provided is substituted in the response
    """
    server_id = server_info["id"]
    data = {"server": {"status": "ACTIVE",
                       "id": server_id,
                       "name": server_info['name'],
                       "flavor": {"id": server_info["flavorRef"],
                                  "links": [{"href": "http://localhost", "rel": "self"}]},
                       "image": {"id": server_info["imageRef"],
                                 "links": [{"href": "http://localhost", "rel": "self"}]},
                       "addresses": {
                           "public": [
                                    {"version": 6,
                                     "addr": "2401:1801:7800:0101:7271:929b:ff18:06de"},
                                    {"version": 4,
                                     "addr": "119.9.41.136"}],
                           "private": [
                                    {"version": 4,
                                     "addr": "10.176.8.{}".format(randrange(255))}]},
                       "metadata": server_info["metadata"],
                       "links": [{
                           "href": "http://localhost:8902/v2/{0}/servers/{1}".format(tenant_id,
                                                                                     server_id),
                           "rel": "self"},
                           {"href": "http://localhost:8902/v2/{0}/servers/{1}".format(tenant_id,
                                                                                      server_id),
                            "rel": "bookmark"}]}}
    server_addresses_cache['server_id'] = {'addresses': data['server']['addresses']}
    return data


def list_addresses(tenant_id, server_id):
    """
    Returns the public and private ip address for the given server
    """
    return server_addresses_cache['server_id']


def create_server_example(tenant_id):
    """
    Canned response for create server
    """
    server_id = 'test-server{0}-id-{0}'.format(str(randrange(9999999999)))
    return {'server':
           {'OS-DCF:diskConfig': 'AUTO',
            'id': server_id,
            'links': [{'href': 'http://localhost:8902/v2/{0}/servers/{1}'.format(tenant_id, server_id),
                       'rel': 'self'},
                      {'href': 'http://localhost:8902/v2/{0}/servers/{1}'.format(tenant_id, server_id),
                       'rel': 'bookmark'}],
            'adminPass': 'testpassword'}}


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
