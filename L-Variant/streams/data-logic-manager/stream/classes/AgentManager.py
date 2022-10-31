from collections import namedtuple

class AgentManager:
    
    def __init__(self):
        self.topics = []
        
    def create_agent(self, start_topic: str, next_topic, fun, data):
        """ 
            creation of a single agent.
    
            `start_topic`:  str
                Just a string that you can use in other functions
                to figure out how messages in that topic can be
                transformed

            `next_topic`:  faust.topics.Topic
                A faust `app.topic` instance
        """

        async def agent(stream):
            """
                send messages from one topic to another
                ...and possibly transform the message before sending
            """
            async for message in stream:
                """
                    Process message
                """ 
                message = await fun(message, data)
            
                if message is not None:
                    await next_topic.send(value=message)
                    print("Following message sucessfully processed: \n" + str(message))
                else:
                    print("Following message failed processing: \n" + str(message))

        return agent

    def agents(self):
        """
            configuration of multiple agents
            ....again, thanks to closures
        """
        agents = []
        for topic in self.topics:
            """ `topic`:  app.topic instance """
            agents.append(
                # `topic.start`: str
                # `topic.next`: faust.topics.Topic
                (self.create_agent(topic.start, topic.next, fun=topic.fun, data=topic.data),
                topic)
            )
        return agents

    def attach_agent(self, app, agent, topic: namedtuple):
        """ Attach the agent to the Faust app """
        # `topic.faust`: faust.topics.Topic
        # it is equivalent to `app.topic(topic.start)`
        app.agent(channel=topic.faust, name=f"{topic.start}-agent")(agent)
