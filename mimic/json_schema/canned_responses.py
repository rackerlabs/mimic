from random import randrange


def get_server(server_id):
    """
    Canned response for get server.
    The server id provided is substituted in the response
    """
    return {'server': {'status': 'ACTIVE', 'id': server_id}}


def create_server_example(tenant_id):
    """
    Canned response for create server
    """
    server_id = 'test-server{0}-id-{0}'.format(str(randrange(9999999999)))
    return {'server':
           {'OS-DCF:diskConfig': 'AUTO',
            'id': server_id,
            'links': [{'href': 'http:localhost/v2/{0}/servers/{1}'.format(tenant_id, server_id),
                       'rel': 'self'},
                      {'href': 'http:localhost/v2/{0}/servers/{1}'.format(tenant_id, server_id),
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
