"""
The usage of this module is solely to
print all containers into the command
line.
"""

__author__ = 'TMO'

import pprint
import sys

import docker
from docker.models.containers import Container

CLIENT = docker.from_env()

SHOW_ALL = bool(sys.argv[1])
COMPONENT_TYPE = str(sys.argv[2])

components = {
    "producers": [
        "opcua",
        "modbus",
        "mqtt",
        "iotsimulator",
        "iiotsimulator"
    ],
    "consumers": [
        "influx",
        "mongo",
        "webhook"
    ],
    "streams": [
        "aggregator",
        "anonymizer",
        "data-logic-manager",
        "payperuse"
    ]
}

component_type_list = components[COMPONENT_TYPE]


def compare(container: Container) -> bool:
    """ Filter function to filter all components
    of the given component type list

    :param container: given docker container
    :return: bool
    """
    for component in component_type_list:
        if container.name.find(component) != -1:
            return True
    return False


containers = filter(compare, CLIENT.containers.list(all=SHOW_ALL))


def convert(container: Container) -> dict:
    """ Read a containers status and convert it into a dict

    :param container: Given container object
    :return: dict
    """
    return {
        'id': container.short_id,
        'name': container.name,
        'started': container.attrs['State']['StartedAt'],
        'status': container.status,
        'network': container.attrs['NetworkSettings']['IPAddress']
    }


pprint.pprint(list(map(convert, containers)))

sys.stdout.flush()
