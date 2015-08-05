"""
Creates a cannned response for list flavors
"""


def create_flavor(flavor_id):
    """
    Populates the flavor template and returns it.
    """
    return {"id": "onmetal-" + str(flavor_id),
            "links": [
                {"href": "http://this-link-is-not-functional/flavors/" + str(flavor_id),
                 "rel": "self"},
                {"href": "http://this-link-is-not-functional/flavors/" + str(flavor_id),
                 "rel": "bookmark"}],
            "name": "{0}GB Instance".format(flavor_id)}


def get_flavor_list(fnum):
    """
    Creates a list of flavors
    :param int fnum: The number of the flavors to populate in the flavor list.
    :return: a 	`list` of flavors
    """
    return {"flavors": [create_flavor(each) for each in range(fnum)]}
