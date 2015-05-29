# -*- test-case-name: mimic.test.test_mailgun -*-
"""
API Mock for Mail Gun.
https://documentation.mailgun.com/api-sending.html
"""

import json
from random import randrange

from mimic.rest.mimicapp import MimicApp
items = {}


class MailGunApi(object):
    """
    Rest endpoints for mocked Mail Gun api.
    """

    app = MimicApp()

    def __init__(self, core):
        """
        :param MimicCore core: The core to which this Mail Gun Api will be
        communicating.
        """
        self.core = core

    @app.route('/messages', methods=['POST'])
    def send_messages(self, request):
        """
        Responds with a 200 with a static response.
        """
        content = str(request.content.read())
        request.setResponseCode(200)
        message_id = randrange(99999999999)
        items.update({message_id: content})
        return json.dumps({
            "message": "Queued. Thank you.",
            "id": "<{0}@samples.mailgun.org>".format(message_id)})

    @app.route('/messages', methods=['GET'])
    def get_message_count(self, request):
        """
        Responds with a 200 and the number of messages POSTed
        through the ``/messages`` endpoint.
        """
        request.setResponseCode(200)
        return json.dumps({"message_count": len(items)})
