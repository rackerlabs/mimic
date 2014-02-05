"""
Defines the preset values in the mimic api.
"""


get_presets = {'loadbalancers': {'failing_lb_id': '175647',
                                 'invalid_lb': '3909',
                                 'return_422_on_add_node_count': 3},
               'servers': {'create_server_failure': {'message': 'given message', 'code': 'given code'},
                           'delete_server_failure': {'code': 'given code', 'times': 'returns given code'
                                                             'that many times'},
                           'invalid_image_ref': ['INVALID-IMAGE-ID', '1111', 'image_ends_with_Z'],
                           'invalid_flavor_ref': ['INVALID-FLAVOR-ID', '8888', '-4', '1'],
                           'server_error': 'sets server state to error on create',
                           'server_building': 'sets the server to be in building state for given time'}
               }
