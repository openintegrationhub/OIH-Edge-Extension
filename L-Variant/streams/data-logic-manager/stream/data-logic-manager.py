from droolsdk.commands.insert_object_command import InsertObjectCommand
from droolsdk.kie.drools import Drools
from droolsdk.exceptions.drools_exception import DroolsException

import faust

from asyncio import sleep
from collections import namedtuple

from component_base_class import ComponentBaseClass as cbc
from classes.AgentManager import AgentManager

cbc = cbc()
logger = cbc.get_logger()
config_template={}
config = cbc.get_config(config_template, source="file")
app_name = config["application_name"]
broker = config["broker"]
app = faust.App(app_name, broker=broker)
agent_manager = AgentManager()

async def _apply_rules(message, container):                 
        # Set configuration variables like your KIE_SERVER credentials, ROOT KIE_SERVER URL and so on
        Drools.KIE_SERVER_CONTAINER_ID = container["container_id"] # Example : Sample_Project_1.0.0-SNAPSHOT
        Drools.KIE_SERVER_CONTAINER_PACKAGE = container["container_package"] # Example: com.myspace.sample_project
        Drools.KIE_SERVER_USERNAME = config["kie_server"]["username"] 
        Drools.KIE_SERVER_PASSWORD = config["kie_server"]["password"] 
        Drools.KIE_SERVER_ROOT_URL = config["kie_server"]["host"] 
        # If you defined a KIE_SESSION in your drools workbench project, you can specify it like the following line
        # Drools.KIE_SESSION_NAME = 'your_kie_session_name'
        
        json_object = container["object"]
        json_object_name = json_object["name"]
        json_object_fields = json_object["fields"]
            
        if message is not None:
            
            Object = namedtuple(json_object_name, json_object_fields) 
            my_object = Object(**message)
           
            # Create an InsertElementsCommand in order to fire rules on a list of object
            # The 'products' parameter represent the list of object to sent, 'out_identifier' should be a unique key
            # that is going to used for extracting the associated products'list after having response from drools kie server
            insert_elements_command = InsertObjectCommand(object=my_object, out_identifier='object').initialize()
            # Add commands before excuting them
            Drools.add_command(insert_elements_command)
            # Execute all commands
            try:
                response = Drools.execute_commands()
                # Getting the list of products after drools rules execution on them by using its respective key
                drools_response = response['object']
                return drools_response
                
            except DroolsException as de:
                print(de)
                logger.error(str(de))
                return ""
            # sleep for 2 seconds
        else:
            logger.info('No message received')
            await sleep(2)

for container in config["kie_server"]["containers"]:
    
    source_topic_name = container["input_topic"]
    output_topic_name = container["output_topic"]
    
    Topic = namedtuple("topic", ["faust", "start", "next", "fun", "data"])
    agent_manager.topics.append(Topic(faust=app.topic(source_topic_name), start=source_topic_name, next=app.topic(output_topic_name), fun=_apply_rules, data=container))

for agent, topic in agent_manager.agents():
    agent_manager.attach_agent(app, agent, topic)

if __name__ == '__main__':
    app.main()