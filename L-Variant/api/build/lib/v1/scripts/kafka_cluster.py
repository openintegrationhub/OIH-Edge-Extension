"""
This script is used as a means to
manage kafka clusters.
"""

__author__ = 'TMO'

import argparse

import docker
import python_on_whales

ENV_LOCATION = "./src/v1/scripts/kafka.env"
SEPERATOR = ','


def print_response(
        compose_client: python_on_whales.DockerClient,
        docker_cli: docker.client.DockerClient):
    """ Print a response to the command line, which consists of
    all parts of the kafka cluster

    :param compose_client: Docker Client which stores the compose file and
    is able to start the cluster
    :param docker_cli: Docker Client which manages all components
    :return: None
    """
    for stats in compose_client.stats(all=True):
        if stats.container_name in ['broker', 'kafka-ui',
                                    'zookeeper']:
            print(f'{stats.container_name}::'
                  f'{docker_cli.containers.get(stats.container_id).status}')


docker_client = docker.from_env()
parser = argparse.ArgumentParser()

parser.add_argument(
    '-c',
    help='Command to be executed',
    choices=['up', 'down', 'start', 'stop', 'kill', 'pause',
             'unpause', 'restart', 'status'],
    type=str,
    required=True,
    dest='C'
)
parser.add_argument(
    '-s',
    '-service',
    help='Execute the given command for the specified'
         'service, if empty execute the command for all'
         'services',
    required=False,
    default=None,
    type=str,
    dest='S'
)
parser.add_argument(
    '-zp',
    '-zookeeper-port',
    help='Port for the zookeeper',
    type=int,
    required=False,
    default=2181,
    dest='ZP'
)
parser.add_argument(
    '-bp',
    '-broker-ports',
    help='Ports for the zookeeper. Only up to 4 args will be '
         'read!',
    type=list,
    required=False,
    default=[9092, 9101, 19092, 29092],
    dest='BP'
)
parser.add_argument(
    '-kp',
    '-kafka-ui-port',
    help='Port for the kafka-ui',
    type=int,
    required=False,
    default=8080,
    dest='KP'
)

args = parser.parse_args()

kafka_client = python_on_whales.DockerClient(
    compose_files=['../docker-compose.yml'],
    compose_env_file=ENV_LOCATION)


def create_env_file():
    """ Create an env file regarding the given arguments of the caller.

    :return: None
    """
    broker_ports = []
    args_default = parser.get_default('BP')
    for arg in args.BP:
        if isinstance(arg, int):
            broker_ports.append(arg)
    if len(broker_ports) < 4:
        for i in range(4):
            if args_default[i] not in broker_ports:
                broker_ports.append(args_default[i])
                if len(broker_ports) == 4:
                    break

    with open(ENV_LOCATION, 'w', encoding='UTF-8') as kafka_file:
        kafka_file.write(f'ZOOKEEPER_PORT={args.ZP}\n')
        for i in range(4):
            kafka_file.write(f'BROKER_PORT_{i}={broker_ports[i]}\n')
        kafka_file.write(f'KAFKA_UI_PORT={args.KP}\n')


if args.C == 'up':
    create_env_file()
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.build(services=services, quiet=True)
        kafka_client.compose.up(services=services, detach=True)
    else:
        kafka_client.compose.build(quiet=True)
        kafka_client.compose.up(detach=True)
    print_response(kafka_client, docker_client)
elif args.C == 'start':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.start(services=services)
    else:
        kafka_client.compose.start()
    print_response(kafka_client, docker_client)
elif args.C == 'stop':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.stop(services=services)
    else:
        kafka_client.compose.stop()
    print_response(kafka_client, docker_client)
elif args.C == 'down':
    kafka_client.compose.down()
    print_response(kafka_client, docker_client)
elif args.C == 'kill':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.kill(services=services)
        kafka_client.compose.rm(services=services)
    else:
        kafka_client.compose.kill()
        kafka_client.compose.rm()
    print_response(kafka_client, docker_client)
elif args.C == 'pause':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.pause(services=services)
    else:
        kafka_client.compose.pause()
    print_response(kafka_client, docker_client)
elif args.C == 'unpause':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.unpause(services=services)
    else:
        kafka_client.compose.unpause()
    print_response(kafka_client, docker_client)
elif args.C == 'restart':
    if args.S:
        services = args.S.split(SEPERATOR)
        kafka_client.compose.restart(services=services)
    else:
        kafka_client.compose.restart()
    print_response(kafka_client, docker_client)
elif args.C == 'status':
    print_response(kafka_client, docker_client)
