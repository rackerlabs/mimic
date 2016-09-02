from __future__ import absolute_import, division, unicode_literals

import ddt
from twisted.trial.unittest import SynchronousTestCase

from mimic.model.identity import TokenCredentials


@ddt.ddt
class TokenCredentialsTest(SynchronousTestCase):
    """
    Test for generating token/tenant credentials
    """

    @ddt.data(
        'tenantId',
        'tenantName'
    )
    def test_from_json(self, field_name):
        """
        Auth Token will be generated with either tenantId or tenantName
        used in the JSON auth data.
        """
        token_value = 'abcdefg'
        id_value = '1234567890'
        json_data = {
            'auth': {
                'token': {
                    'id': token_value
                },
                field_name: id_value
            },
        }
        token_credentials = TokenCredentials.from_json(json_data)
        self.assertEqual(token_credentials.tenant_id, id_value)
        self.assertEqual(token_credentials.token, token_value)
        self.assertEqual(token_credentials.type_key, 'token')
