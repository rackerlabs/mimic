# -*- test-case-name: mimic.test.test_ironic -*-
"""
API Mock for Ironic.
http://docs.openstack.org/developer/ironic/webapi/v1.html
"""

from mimic.rest.mimicapp import MimicApp


class IronicApi(object):
    """
    Rest endpoints for the Ironic API.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which the Ironic Api will be
        communicating.
        """
        self.core = core

    @app.route('/nodes', methods=['POST'])
    def create_node(self, request):
        """
        Responds with response code 201 and returns the newly created node.
        """
        return self.core.ironic_node_store.create_node(request)

    @app.route('/nodes/<string:node_id>', methods=['DELETE'])
    def delete_node(self, request, node_id):
        """
        Responds with response code 204 and delete the node.
        """
        return self.core.ironic_node_store.delete_node(request, node_id)

    @app.route('/nodes', methods=['GET'])
    def list_nodes(self, request):
        """
        Responds with response code 200 with a list of nodes.
        """
        return self.core.ironic_node_store.list_nodes(include_details=False)

    @app.route('/nodes/detail', methods=['GET'])
    def list_nodes_with_details(self, request):
        """
        Responds with response code 200 with a list of nodes and its details.
        """
        return self.core.ironic_node_store.list_nodes(include_details=True)

    @app.route('/nodes/<string:node_id>', methods=['GET'])
    def get_node_details(self, request, node_id):
        """
        Responds with response code 200 with details of the nodes.
        """
        return self.core.ironic_node_store.get_node_details(request, node_id)

    @app.route('/nodes/<string:node_id>/states/provision', methods=['PUT'])
    def set_node_provision_state(self, request, node_id):
        """
        Responds with response code 202 and sets the provision state of
        the node.
        """
        return self.core.ironic_node_store.set_node_provision_state(
            request, node_id)

    @app.route('/nodes/<string:node_id>/vendor_passthru/<string:method>', methods=['POST'])
    def vendor_passthru_cache_image(self, request, node_id, method):
        """
        Responds with response code 202 and sets the :obj:`Node`'s cache_image_id
        and cache_status.
        Returns 400 if `node_id` does not exist or if the `method` is not `cache_image`
        """
        return self.core.ironic_node_store.cache_image_using_vendor_passthru(
            request, node_id, method)
