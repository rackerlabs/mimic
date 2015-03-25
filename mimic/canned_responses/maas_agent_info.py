"""
Canned response for monitoring agent info
"""


def agent_info(entity_id, agent_id):
    """
    Return example agent info from a windows machine
    """
    return {
        "values": [
            {
                "agent_id": agent_id,
                "entity_id": entity_id,
                "entity_uri": "https://ord.servers.api.mimic.co.jp/" + agent_id,
                "host_info": {
                    "memory": {
                        "timestamp": 1423092674788,
                        "error": None,
                        "info": {
                            "used_percent": 36.033373792207,
                            "swap_free": 3406512128,
                            "free": 1311469568,
                            "swap_page_out": 3072,
                            "swap_used": 883855360,
                            "swap_total": 4290367488,
                            "actual_used": 772153344,
                            "swap_page_in": 59260928,
                            "total": 2142883840,
                            "free_percent": 63.966626207793,
                            "ram": 2048,
                            "actual_free": 1370730496,
                            "used": 831414272
                        }
                    },
                    "disks": {
                        "timestamp": 1423092675911,
                        "error": None,
                        "info": [
                            {
                                "name": "C:\\",
                                "wtime": 2718909792,
                                "rtime": 2718909792,
                                "read_bytes": 223028736,
                                "write_bytes": 561209344,
                                "time": 2718909792,
                                "writes": 135069,
                                "reads": 4425
                            }
                        ]
                    },
                    "filesystems": {
                        "timestamp": 1423092675911,
                        "error": None,
                        "info": [
                            {
                                "free": 64707132,
                                "avail": 64707132,
                                "dev_name": "C:\\",
                                "total": 83884028,
                                "sys_type_name": "NTFS",
                                "options": "rw",
                                "dir_name": "C:\\",
                                "used": 19176896
                            }
                        ]
                    },
                    "cpus": {
                        "timestamp": 1423092675911,
                        "error": None,
                        "info": [
                            {
                                "name": "cpu.0",
                                "vendor": "AMD",
                                "user": 36619627,
                                "model": "Opteron",
                                "total_sockets": 2,
                                "total_cores": 2,
                                "idle": 1714740481,
                                "total": 1801677388,
                                "sys": 50317280,
                                "mhz": 2094
                            },
                            {
                                "name": "cpu.1",
                                "vendor": "AMD",
                                "user": 20848223,
                                "model": "Opteron",
                                "total_sockets": 2,
                                "total_cores": 2,
                                "idle": 1749752815,
                                "total": 1801675750,
                                "sys": 31074712,
                                "mhz": 2094
                            }
                        ]
                    }
                }
            }
        ],
        "metadata": {
            "count": 1,
            "limit": 100,
            "marker": None,
            "next_marker": None,
            "next_href": None
        }
    }
