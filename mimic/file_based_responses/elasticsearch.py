"""
Deterministic response for ElasticSearch requests
"""

import json

from twisted.python import log


class ElasticSearchResponse():

    """
    Deterministic response for ElasticSearch requests.
    """

    def health(self):
        """
        Returns that ElasticSearch API is alive
        """
        return {'ES status': 'ok'}

    def version(self):
        """
        Returns ElasticSearch API version information.
        """
        return {'ES status': 'ok', 'version': '0.0.0.001'}

    def search(self, indexes, types, args, request_data):
        """
        Returns response data based on specified indexes and types
        """
        try:
            # assume everything is going to work
            response_code = 200

            # load the cached ElasticSearch data from file
            es_data_filepath = \
                'mimic/file_based_responses/json_files/elasticsearch.json'
            es_data = json.load(open(es_data_filepath))

            # preserve order of data from file
            sorted_es_data = sorted(es_data, key=lambda dict: dict['order_key'])

            response = None
            # loop on the responses, looking for an index and type match
            for es_data_element in sorted_es_data:
                if (indexes[0] == 'ALL' or es_data_element["index"] in indexes)\
                    and\
                   (types[0] == 'ALL' or es_data_element["type"] in types):
                    response = es_data_element["response"]
                    break

            if response == None:
                # something is wrong with the request; i.e. response is not
                # available in the data file for requested index and/or type
                response_code = 400
                response = {'message':
                            ('response for index/type not available in'
                             ' ElasticSearch data file [elasticsearch.json]')}

            log.msg("\n{'ES status': 'ok', 'indexes': " + ",".join(indexes) +
                    ", 'types': " + ",".join(types) +
                    "\n'args':" + str(args) +
                    "\n'url_data':" + str(request_data) +
                    "\n'response': " + str(response) + "}")

        except Exception as e:
            # server side problem processing request
            response_code = 500
            response = {'message':
                        ('Exception occurred processing ElasticSearch request!'
                         ' e: %s' % str(e))}

        return response_code, response
