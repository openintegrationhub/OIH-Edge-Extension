"""
This module is used to manage all container running
in the system.
"""

__author__ = 'TMO/MGR'

import pprint
import sys
import time

import docker
from docker.models.containers import Container


def convert(container: Container):
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


def print_response():
    """ Print the container name, id and status into
    the console.

    :return: None
    """
    container = client.containers.get(sys.argv[1])
    pprint.pprint(
        {
            'container': container.name,
            'container_id': container.short_id,
            'status': container.status
        }
    )


client = docker.from_env()

con = client.containers.get(sys.argv[1])

choice = sys.argv[2]

if choice == 'start':
    if con.status != 'running':
        con.start()
elif choice == 'stop':
    if con.status == 'running':
        con.stop()
elif choice == 'restart':
    con.restart()
elif choice == 'pause':
    if con.status == 'running':
        con.pause()
elif choice == 'unpause':
    if con.status == 'paused':
        con.unpause()
elif choice == 'remove':
    con.stop()
    while con.status == 'running':
        con = client.containers.get(sys.argv[1])
        time.sleep(1)
        print(con)
    con.remove()
elif choice == 'get':
    pprint.pprint(convert(container=con))
elif choice == 'getPathname':
    attr = con.attrs
    for entry in attr['Config']['Env']:
        if entry.find('path_name') != -1:
            print(entry.replace('path_name=', ''), end="")

if choice not in ['get', 'getPathname']:
    print_response()

sys.stdout.flush()
