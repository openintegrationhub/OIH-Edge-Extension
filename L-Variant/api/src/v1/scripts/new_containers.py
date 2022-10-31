"""
The usage of this module is to create new
docker container, in regard to the given
arguments of the caller.
"""

__author__ = 'TMO'

import pprint
import re
import sys

import docker
from python_on_whales import DockerClient as wh_client

ENV_LOCATION = "./src/v1/scripts/.env"


def count_container(name: str, docker_client: docker.client):
    """ Count the number of instances of the given component
    and return the name concatenated with the number + 1

    :param name: container name
    :param docker_client: docker client
    :return: (str) container name
    """
    containers = docker_client.containers.list(all=True)
    count = 1
    for con in containers:
        if re.match(f'.?({name})[^$]*', con.name):
            count += 1

    con_name = f'{name}_{count}'

    with open(ENV_LOCATION, "w", encoding='UTF-8') as base_env_file:
        base_env_file.write(f'CONNAME="{con_name}"\n')
        base_env_file.write(f'PATHNAME="{con_name}"\n')

    return con_name


client = docker.from_env()
container_name = sys.argv[1]

con_name = count_container(container_name, client)

if container_name == 'opcua':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../producers/opcua/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'iiotsimulator':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../producers/iiotsimulator/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'iotsimulator':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../producers/iotsimulator/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'modbus':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../producers/modbus/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'mqtt':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../producers/mqtt/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'aggregator':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../streams/aggregator/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'anonymizer':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../streams/anonymizer/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'data-logic-manager':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../streams/data-logic-manager/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'payperuse':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../streams/payperuse/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'influx':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../consumers/influx/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'mongodb':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../consumers/mongodb/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
elif container_name == 'webhook':
    app_client = wh_client(
        compose_project_name=con_name,
        compose_files=[
            '../consumers/webhook/docker-compose.yml'],
        compose_env_file=ENV_LOCATION)
else:
    print('No valid Container name given!', flush=True)
    sys.exit(22)


def print_response(container_list: list, path_name: str):
    """ Print a response into the command link.

    :param container_list: list of all container created by the project
    :param path_name: (str) path name of the config file of the component
    :return: None
    """
    for container in container_list:
        if path_name == container.name:
            pprint.pprint({
                'container': path_name,
                'container_id': container.id[0:9],
                'status': container.state.status
            })


if app_client:
    app_client.compose.build(quiet=True)
    app_client.compose.up(detach=True)
    print_response(app_client.compose.ps(), con_name)
    sys.exit(0)
