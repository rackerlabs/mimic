"""
Canned responses for MAAS monitoring zones.
"""


def monitoring_zones():
    """
    Canned response for the /monitoring_zones call.
    """
    return [{
        "id": "mzdfw",
        "label": "Dallas Fort Worth (DFW)",
        "country_code": "US",
        "source_ips": [
            "dead:beef:cafe:face::/64",
            "1.2.3.128/26"
        ]
    }, {
        "id": "mzhkg",
        "label": "Hong Kong (HKG)",
        "country_code": "HK",
        "source_ips": [
            "4.5.6.64/26",
            "1337:f005:ba11:d00d:0:0:0:0/64"
        ]
    }, {
        "id": "mziad",
        "label": "Northern Virginia (IAD)",
        "country_code": "US",
        "source_ips": [
            "5ca1:ab1e:7e1e:ca57::/64",
            "7.8.9.192/26"
        ]
    }, {
        "id": "mzlon",
        "label": "London (LON)",
        "country_code": "GB",
        "source_ips": [
            "1ceb:00da:8bad:food::/64",
            "11.12.13.0/26"
        ]
    }, {
        "id": "mzord",
        "label": "Chicago (ORD)",
        "country_code": "US",
        "source_ips": [
            "ba5e:ba11:1111:2222::/64",
            "14.15.16.0/26"
        ]
    }, {
        "id": "mzsyd",
        "label": "Sydney (SYD)",
        "country_code": "AU",
        "source_ips": [
            "17.18.19.0/26",
            "1111:2222:3333:4444::/64"
        ]
    }]
