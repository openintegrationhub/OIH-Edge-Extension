
import faust

#__all__ = ["create_app"]

def create_app(config):
    """Create and configure a Faust based kafka-aggregator application.
    Parameters
    ----------
    config : `Configuration`, optional
        The configuration to use.  If not provided, the default
        :ref:`Configuration` will be used.
    """

    print("Kafka Broker is",config['broker'])
    app = faust.App(
        id="kafkaaggregator",
        broker=config['broker'])

    return app



'''config =  {
    "broker":"kafka://localhost:9092"
}

print('in app')
app: faust.App = create_app(config)'''