from random import randrange


def get_server(tenant_id, server_id):
    """
    Canned response for get server.
    The server id provided is substituted in the response
    """
    return {"server": {"status": "ACTIVE",
                       "id": server_id,
                       "name": 'server-from-above',
                       "addresses": {
                           "public": [
                                    {"version": 6,
                                     "addr": "2401:1801:7800:0101:7271:929b:ff18:06de"},
                                    {"version": 4,
                                     "addr": "119.9.41.136"}],
                           "private": [
                                    {"version": 4,
                                     "addr": "10.176.8.186"}]},
                       "links": [{
                           "href": "http://localhost:8909/v2/{0}/servers/{1}".format(tenant_id,
                                                                                     server_id),
                           "rel": "self"},
                           {"href": "http://localhost:8909/v2/{0}/servers/{1}".format(tenant_id,
                                                                                      server_id),
                            "rel": "bookmark"}]}}


def create_server_example(tenant_id):
    """
    Canned response for create server
    """
    server_id = 'test-server{0}-id-{0}'.format(str(randrange(9999999999)))
    return {'server':
           {'OS-DCF:diskConfig': 'AUTO',
            'id': server_id,
            'links': [{'href': 'http://localhost:8909/v2/{0}/servers/{1}'.format(tenant_id, server_id),
                       'rel': 'self'},
                      {'href': 'http://localhost:8909/v2/{0}/servers/{1}'.format(tenant_id, server_id),
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


def list_server(tenant_id, server_name):
    """
    Canned response for the list servers.
    """
    return {'id': 'server_id',
            'name': server_name,
            "links": [{
                      "href": "http://localhost:8909/v2/{0}/servers/".format(tenant_id),
                      "rel": "self"},
                      {"href": "http://localhost:8909/v2/{0}/servers".format(tenant_id),
                       "rel": "bookmark"}]}
